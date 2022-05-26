import socket, sys, json, youtube_dl, validators, urllib

d = dict()
ydl_opts = {
    'outtmpl': './%(extractor_key)s/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

def universal_conversion(data):
    if isinstance(data, bytes):
        return json.loads(data.decode("utf-8"))
    if not isinstance(data, str):
        data = json.dumps(data)
    
    return bytes(data, "utf-8")

def download_videos(s):
    links = []
    keep_asking = True
    while keep_asking:
        i = input("Enter a youtube link or press enter to download:\n")
        if len(i) > 1:
            if not validators.url(i):
                print("Not an URL.")
                continue
            if "youtube.com" not in urllib.parse.urlparse(i).hostname:
                print("domain is not youtube.com.")
                continue
            links.append(i)
        else:
            keep_asking = False
    print("Gotcha. Sending {} link{} to the server...".format(len(links), "s" if len(links) > 0 else ""))
    data = universal_conversion({
        "choice":"download",
        "payload":links
        })
    s.sendall(data)
    data = s.recv(1024)
    print(f"Received {data!r}")

for a in sys.argv[1:]:
    print(a)
    a = a.strip("-")
    if "=" not in a:
        d[a] = True
    else:
        k, v = a.split("=")
        d[k] = v
sock = None


if "server" in d and d["server"] == True:
    HOST = "127.0.0.1"
    PORT = int(d.get("port", 65432))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                data = conn.recv(1024)
                try:
                    data = universal_conversion(data)
                    if data["choice"] == "download":
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                            ydl.cache.remove()

                            download_rtn = ydl.download(data["payload"])
                            conn.sendall(universal_conversion(download_rtn))
                    if data["choice"] == "change_dir":
                        data["payload"] = data["payload"] + "/" if data["payload"][-1] != "/" else data["payload"]
                        ydl_opts["outtmpl"] = data["payload"] + "%(extractor_key)s/%(extractor)s-%(id)s-%(title)s.%(ext)s"
                        conn.sendall(universal_conversion("done"))
                except Exception as e:

                    conn.sendall(universal_conversion(str(e)))
                    data = None
                    continue
                data = None
else:
    HOST = d["address"]  # The server's hostname or IP address
    PORT = int(d.get("port", 65432))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Connected.")
        in_session = True
        while in_session:
            choice = int(input("Enter 1 to download videos or 2 to set the target directory:"))
            if choice == 1:
                download_videos(s)
                i = input("Do you have more links to download? (Y/n)")
                in_session = "n" not in i 
            if choice == 2:
                new_path = input("Enter the new path:\n")
                data = universal_conversion({
                    "choice":"change_dir",
                    "payload":new_path
                    })
                s.sendall(data)
                data = s.recv(1024)
                print(f"Received {data!r}")
                        


