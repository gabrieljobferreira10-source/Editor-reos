import streamlit as st, subprocess, tempfile, os, re

def montar_edicao(prompt):
    p = prompt.lower()
    f = []
    if "parad" in p or "trav" in p:
        f.append("mpdecimate,setpts=N/FRAME_RATE/TB")
    if "trem" in p or "estabil" in p:
        f.append("deshake")
    vel = re.search(r"(\d+(?:[.,]\d+)?)\s*x", p)
    if vel:
        f.append(f"setpts=PTS/{vel.group(1).replace(',', '.')}")
    f.append("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'")
    f.append("scale=1080:1920:flags=lanczos")
    if "zoom" in p:
        f.append("zoompan=z='min(zoom+0.0015,1.25)':x='iw/2-(iw/zoom/2)':"
                 "y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30")
    if "nitid" in p or "qualidade" in p:
        f.append("unsharp=5:5:0.8")
    if "cor" in p or "vivo" in p:
        f.append("eq=contrast=1.1:saturation=1.25")
    cadeia = ",".join(f)

    if "ida e volta" in p or "revers" in p:
        fc = (f"[0:v]{cadeia},split[a][b];"
              "[b]trim=0:1.5,setpts=PTS-STARTPTS,split[c][d];[d]reverse[r];"
              "[c][r][a]concat=n=3:v=1:a=0[out]")
    else:
        fc = f"[0:v]{cadeia}[out]"

    dur = re.search(r"(\d+)\s*(s|seg)", p)
    return fc, (dur.group(1) if dur else None)

st.title("🎬 Editor de Reels")
video = st.file_uploader("Envie seu vídeo", type=["mp4", "mov"])
prompt = st.text_area("O que você quer?",
    "estabilizar, cortar paradas, zoom, ida e volta, qualidade, cor, 30s")

if video and st.button("Editar"):
    with tempfile.TemporaryDirectory() as d:
        ent, sai = os.path.join(d, "in.mp4"), os.path.join(d, "out.mp4")
        open(ent, "wb").write(video.read())
        fc, dur = montar_edicao(prompt)
        cmd = ["ffmpeg", "-y", "-i", ent, "-filter_complex", fc, "-map", "[out]",
               "-an", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
               "-pix_fmt", "yuv420p"]
        if dur: cmd += ["-t", dur]
        with st.spinner("Editando..."):
            subprocess.run(cmd + [sai], check=True)
        st.video(sai)
        st.download_button("Baixar vídeo", open(sai, "rb"), "reels_editado.mp4")

