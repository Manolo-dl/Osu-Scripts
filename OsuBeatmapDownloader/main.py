import threading
from platform import system
from Addons.get_cookie import get_cookie
from Addons.get_file import get_file
from Addons.get_links_list import get_links_list
from Scripts.start_download import start_download
from Scripts.start_threads import thread_get_folder, results

if __name__ == '__main__':

    osu_path_thread = threading.Thread(target=thread_get_folder)
    osu_path_thread.start()

    osu_cookie = get_cookie(
        "config.json",
        "a.js-current-user-avatar.js-user-login--menu",
        "osu_session",
        "https://osu.ppy.sh/"
    )

    osu_path_thread.join()
    start_download(
        osu_cookie,
        results["osu_path"],
        get_links_list(get_file(), r"https://osu\.ppy\.sh/beatmapsets/\d+#(osu|mania|fruits|taiko)/\d+")
    )