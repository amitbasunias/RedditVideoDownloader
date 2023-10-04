from flask import Flask, render_template, request, send_file
import requests
import os
import time
import threading
import ffmpeg
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)

def download_video(giveurl):
    parsed_url = urlparse(giveurl)
    parsed_url = parsed_url._replace(path=parsed_url.path + '/')
    url = urlunparse(parsed_url) + ".json"
    headers = {
        "User-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36"
    }

    try:
        for retry in range(5):
            try:
                r = requests.get(url, headers=headers, timeout=20)
                r.raise_for_status()
                data = r.json()[0]
                video_url = data["data"]["children"][0]["data"]["secure_media"]["reddit_video"]["fallback_url"]

                title = data["data"]["children"][0]["data"]["title"]
                final_url = "https://v.redd.it/" + video_url.split("/")[3]+'/HLSPlaylist.m3u8'
                output_filename = f"{title}.mp4"

                ffmpeg.input(final_url).output(output_filename, codec="copy").run()

                return output_filename

            except (requests.RequestException, ValueError) as e:
                if retry < 4:
                    time.sleep(2)
                else:
                    return None

    except KeyboardInterrupt:
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        giveurl = request.form.get("giveurl")
        if giveurl:
            output_filename = download_video(giveurl)
            if output_filename:
                return render_template("index.html", output_filename=output_filename)
            else:
                return "An error occurred during download."

    return render_template("index.html")


def delete_file_after_delay(file_path, delay_seconds):
    try:
        time.sleep(delay_seconds)
        os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")


@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(app.root_path, filename)

    delete_thread = threading.Thread(target=delete_file_after_delay, args=(file_path, 300))
    delete_thread.daemon = True  # Mark the thread as daemon to avoid blocking app termination
    delete_thread.start()

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)