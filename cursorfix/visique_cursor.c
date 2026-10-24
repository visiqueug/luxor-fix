/*
 * VISIQUE Luxor Fix - gameplay cursor hider.
 *
 * Loaded by core.dll!LoadGraphicsAPI via luxor.ini (GraphicsAPI_1). Forwards
 * CreateGfxSubsystem to the original gfx2d_dx8.dll unchanged and hides the
 * Windows cursor while the "Game" dialog is the top-most ui2 dialog
 * (i.e. during actual gameplay).
 *
 * The window procedure chain (game -> dgVoodoo) is never modified. Instead a
 * thread timer polls the dialog state and a thread-local WH_CALLWNDPROCRET
 * hook re-applies SetCursor(NULL) after each WM_SETCURSOR has been handled.
 * Both run on the game's main thread (Platform::MessagePump dispatches all
 * thread messages), so ui2 state is only read from the thread that owns it.
 *
 * Offsets verified statically for Luxor 1.0.5.34 (Steam):
 *   ui2.dll  g_ui -> uiSubsystem*, [ui+0x2C] -> dialog stack node,
 *            [node] -> uiDialog*, widget name char[] at +0x1C
 * Any other ui2.dll build disables the cursor logic (forwarding only).
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#define UI2_TIMESTAMP   0x42cb840fu
#define UI2_IMAGESIZE   0x2e000u
#define OFS_DIALOG_TOP  0x2C
#define OFS_WIDGET_NAME 0x1C
#define TIMER_MS        100

typedef void *(__stdcall *CreateGfxFn)(void);
typedef HWND (__cdecl *GetWindowFn)(void);

static HMODULE g_self;
static CreateGfxFn g_realCreate;
static GetWindowFn g_getWindow;
static void **g_uiPtr;
static HHOOK g_hook;
static int g_armed;
static int g_inGame = -1;
static char g_lastName[64];
static FILE *g_log;

static void vqlog(const char *fmt, ...)
{
    if (!g_log) {
        char path[MAX_PATH];
        DWORD n = GetModuleFileNameA(g_self, path, MAX_PATH);
        while (n && path[n - 1] != '\\') n--;
        strcpy(path + n, "visique_cursor.log");
        g_log = fopen(path, "w");
        if (!g_log) return;
    }
    va_list ap;
    va_start(ap, fmt);
    vfprintf(g_log, fmt, ap);
    va_end(ap);
    fputc('\n', g_log);
    fflush(g_log);
}

static int ui2_supported(HMODULE ui2)
{
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)ui2;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((BYTE *)ui2 + dos->e_lfanew);
    vqlog("ui2.dll timestamp=0x%08lx size=0x%lx",
          (unsigned long)nt->FileHeader.TimeDateStamp,
          (unsigned long)nt->OptionalHeader.SizeOfImage);
    return nt->FileHeader.TimeDateStamp == UI2_TIMESTAMP &&
           nt->OptionalHeader.SizeOfImage == UI2_IMAGESIZE;
}

/* Returns the name of the top-most dialog, or NULL. Main thread only. */
static const char *top_dialog_name(void)
{
    BYTE *ui = g_uiPtr ? (BYTE *)*g_uiPtr : NULL;
    if (!ui) return NULL;
    BYTE **node = *(BYTE ***)(ui + OFS_DIALOG_TOP);
    if (!node || !*node) return NULL;
    return (const char *)(*node + OFS_WIDGET_NAME);
}

/* True if the cursor is inside the client area of the active game window. */
static int cursor_over_game(void)
{
    HWND hwnd = g_getWindow();
    POINT pt;
    RECT rc;
    if (!hwnd || GetForegroundWindow() != hwnd || !GetCursorPos(&pt)) return 0;
    if (!GetClientRect(hwnd, &rc)) return 0;
    ScreenToClient(hwnd, &pt);
    return PtInRect(&rc, pt);
}

static void CALLBACK on_timer(HWND hwnd, UINT msg, UINT_PTR id, DWORD time)
{
    (void)hwnd; (void)msg; (void)id; (void)time;
    const char *name = top_dialog_name();
    char cur[64] = "";
    if (name) {
        strncpy(cur, name, sizeof cur - 1);
        cur[sizeof cur - 1] = 0;
    }
    if (strcmp(cur, g_lastName) != 0) {
        vqlog("top dialog: \"%s\"", cur);
        strcpy(g_lastName, cur);
    }
    int inGame = strcmp(cur, "Game") == 0;
    if (inGame != g_inGame) {
        g_inGame = inGame;
        vqlog("gameplay cursor %s", inGame ? "hidden" : "shown");
        if (!inGame && cursor_over_game())
            SetCursor(LoadCursorA(NULL, (LPCSTR)IDC_ARROW));
    }
    if (inGame && cursor_over_game())
        SetCursor(NULL);
}

/* Runs after the window procedure handled a message; never alters results. */
static LRESULT CALLBACK on_wndproc_ret(int code, WPARAM wp, LPARAM lp)
{
    if (code == HC_ACTION && g_inGame == 1) {
        const CWPRETSTRUCT *m = (const CWPRETSTRUCT *)lp;
        if (m->message == WM_SETCURSOR && LOWORD(m->lParam) == HTCLIENT &&
            m->hwnd == g_getWindow())
            SetCursor(NULL);
    }
    return CallNextHookEx(g_hook, code, wp, lp);
}

/* Called on the game's main thread (from CreateGfxSubsystem). */
static void init_cursor_logic(void)
{
    HMODULE ui2 = GetModuleHandleA("ui2.dll");
    HMODULE core = GetModuleHandleA("core.dll");
    if (!ui2 || !core) {
        vqlog("ui2.dll/core.dll not loaded - cursor logic disabled");
        return;
    }
    if (!ui2_supported(ui2)) {
        vqlog("unsupported ui2.dll build - cursor logic disabled");
        return;
    }
    g_uiPtr = (void **)GetProcAddress(ui2, "?g_ui@@3PAVuiSubsystem@@A");
    g_getWindow = (GetWindowFn)GetProcAddress(core, "?GetWindow@Platform@@YAPAUHWND__@@XZ");
    if (!g_uiPtr || !g_getWindow) {
        vqlog("required exports missing - cursor logic disabled");
        return;
    }
    HWND hwnd = g_getWindow();
    DWORD tid = GetCurrentThreadId();
    vqlog("init on thread %lu, window %p (owner thread %lu)", (unsigned long)tid,
          (void *)hwnd, hwnd ? (unsigned long)GetWindowThreadProcessId(hwnd, NULL) : 0ul);
    if (!SetTimer(NULL, 0, TIMER_MS, on_timer)) {
        vqlog("SetTimer failed (%lu) - cursor logic disabled", GetLastError());
        return;
    }
    g_hook = SetWindowsHookExA(WH_CALLWNDPROCRET, on_wndproc_ret, NULL, tid);
    vqlog("cursor logic armed (hook %s)", g_hook ? "ok" : "failed");
}

__declspec(dllexport) void *__stdcall CreateGfxSubsystem(void)
{
    if (!g_realCreate) {
        char path[MAX_PATH];
        DWORD n = GetModuleFileNameA(g_self, path, MAX_PATH);
        while (n && path[n - 1] != '\\') n--;
        strcpy(path + n, "gfx2d_dx8.dll");
        HMODULE real = LoadLibraryExA(path, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
        if (!real) {
            vqlog("failed to load %s (error %lu)", path, GetLastError());
            return NULL;
        }
        g_realCreate = (CreateGfxFn)GetProcAddress(real, "CreateGfxSubsystem");
        if (!g_realCreate) {
            vqlog("gfx2d_dx8.dll has no CreateGfxSubsystem");
            return NULL;
        }
        vqlog("VISIQUE cursor fix: forwarding to %s", path);
    }
    if (!g_armed) {
        g_armed = 1;
        init_cursor_logic();
    }
    return g_realCreate();
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        g_self = inst;
        DisableThreadLibraryCalls(inst);
    }
    return TRUE;
}
