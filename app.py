import streamlit as st, subprocess, tempfile, os, glob

def rodar(cmd):
    subprocess.run(cmd, check=True, capture_output=True)

def preparar(ent, sai, p, d, i):
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
    rodar(["ffmpeg", "-y", "-i", ent, "-vf", ",".join(f), "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", sai])

st.set_page_config(page_title="Nosso Pintor - Editor", page_icon="🎨")

logos = [x for x in glob.glob("*") if x.lower().endswith((".png", ".jpg", ".jpeg"))]
if logos:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(logos[0], use_container_width=True)
st.markdown(" Nosso "
            "Pintor "
            " Editor de Reels ",
            unsafe_allow_html=True)

videos = st.file_uploader("Envie um ou mais vídeos (na ordem)", type=["mp4", "mov"],
                          accept_multiple_files=True)
musica = st.file_uploader("Música (opcional, sua própria)", type=["mp3", "m4a", "wav"])
prompt = st.text_area("O que você quer?",
    "estabilizar, cortar paradas, ida e volta, zoom, qualidade, cor, 30s")

if videos and st.button("Editar", use_container_width=True):
    p = prompt.lower()
    with tempfile.TemporaryDirectory() as d:
        try:
            partes = []
            barra = st.progress(0, "Preparando os vídeos...")
            for i, v in enumerate(videos):
                ent = os.path.join(d, f"in{i}.mp4")
                open(ent, "wb").write(v.read())
                sai = os.path.join(d, f"p{i}.mp4")
                preparar(ent, sai, p, d, i)
                partes.append(sai)
                barra.progress((i + 1) / (len(videos) + 1), f"Vídeo {i+1} de {len(videos)} pronto")

            lista = os.path.join(d, "lista.txt")
            open(lista, "w").write("".join(f"file '{x}'\n" for x in partes))
            junto = os.path.join(d, "junto.mp4")
            rodar(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", junto])

            final = os.path.join(d, "final.mp4")
            cmd = ["ffmpeg", "-y", "-i", junto]
            if musica:
                mus = os.path.join(d, "musica")
                open(mus, "wb").write(musica.read())
                cmd += ["-i", mus]
            if "ida e volta" in p or "revers" in p:
                zoom = ",crop=iw*0.85:ih*0.85,scale=1080:1920" if "zoom" in p else ""
                fc = ("[0:v]split[a][b];[b]trim=0:1.5,setpts=PTS-STARTPTS" + zoom +
                      ",split[c][e];[e]reverse[r];[c][r][a]concat=n=3:v=1:a=0[out]")
            else:
                fc = "[0:v]null[out]"
            cmd += ["-filter_complex", fc, "-map", "[out]"]
            if musica:
                cmd += ["-map", "1:a", "-c:a", "aac", "-shortest"]
            for palavra in p.replace(",", " ").split():
                if palavra.endswith("s") and palavra[:-1].isdigit():
                    cmd += ["-t", palavra[:-1]]
                    break
            cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", final]
            barra.progress(0.95, "Finalizando...")
            rodar(cmd)
            barra.progress(1.0, "Pronto!")
            dados = open(final, "rb").read()
            st.video(dados)
            st.download_button("Baixar vídeo", dados, "nosso_pintor_reels.mp4",
                               use_container_width=True)
        except subprocess.CalledProcessError as e:
            st.error("Deu erro na edição. Tente com vídeos menores.")
            st.code(e.stderr.decode(errors="ignore")[-800:])
