import streamlit as st, subprocess, tempfile, os, glob

FOTOS = (".jpg", ".jpeg", ".png")

def rodar(cmd):
    subprocess.run(cmd, check=True, capture_output=True)

def preparar_foto(ent, sai, i):
    if i % 2 == 0:
        zp = ("zoompan=z='min(zoom+0.0015,1.25)':x='iw/2-(iw/zoom/2)':"
              "y='ih/2-(ih/zoom/2)':d=75:s=1080x1920:fps=30")
    else:
        zp = ("zoompan=z=1.2:x='(iw-iw/zoom)*on/75':"
              "y='ih/2-(ih/zoom/2)':d=75:s=1080x1920:fps=30")
    vf = ("scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
          + zp + ",setsar=1,format=yuv420p")
    rodar(["ffmpeg", "-y", "-i", ent, "-vf", vf,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", sai])

def preparar_video(ent, sai, p, d, i):
    f = []
    if "estabil" in p or "trem" in p:
        trf = os.path.join(d, f"t{i}.trf")
        rodar(["ffmpeg", "-y", "-i", ent, "-vf",
               f"vidstabdetect=shakiness=8:accuracy=15:result={trf}", "-f", "null", "-"])
        f.append(f"vidstabtransform=input={trf}:smoothing=30:zoom=5")
    if "parad" in p:
        f.append("mpdecimate,setpts=N/FRAME_RATE/TB")
    f.append("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'")
    f.append("scale=1080:1920:flags=lanczos,fps=30,setsar=1")
    if "nitid" in p or "qualidade" in p:
        f.append("unsharp=5:5:0.6")
    if "cor" in p:
        f.append("eq=contrast=1.1:saturation=1.25")
    f.append("format=yuv420p")
    r
