import subprocess
import tempfile
from pathlib import Path

import marketing_analytics.main as main_mod


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _clonar(remoto: Path, destino: Path) -> Path:
    subprocess.run(["git", "clone", str(remoto), str(destino)], check=True, capture_output=True, text=True)
    _git("config", "user.email", "test@example.com", cwd=destino)
    _git("config", "user.name", "Test", cwd=destino)
    return destino


def _preparar_remoto_y_clon() -> tuple[Path, Path]:
    """Crea un repo remoto ("bare") con una rama main y un primer commit,
    y un clon local listo para usar como repo_root en los tests."""
    carpeta = Path(tempfile.mkdtemp())
    remoto = carpeta / "remoto.git"
    subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(remoto)], check=True, capture_output=True)

    semilla = carpeta / "semilla"
    _clonar(remoto, semilla)
    (semilla / "README.md").write_text("inicial\n", encoding="utf-8")
    _git("add", "README.md", cwd=semilla)
    _git("commit", "-m", "inicial", cwd=semilla)
    _git("push", "origin", "main", cwd=semilla)

    repo_root = carpeta / "repo"
    _clonar(remoto, repo_root)
    return remoto, repo_root


def test_publica_normalmente_cuando_nadie_mas_pusheo(tmp_path):
    _remoto, repo_root = _preparar_remoto_y_clon()
    ruta_html = tmp_path / "ControlContenido.html"
    ruta_html.write_text("<html>v1</html>", encoding="utf-8")

    main_mod.publicar_github_pages(ruta_html, repo_root=repo_root)

    log = subprocess.run(
        ["git", "log", "--oneline", "-1"], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout
    assert "dashboard: actualizar ControlContenido.html" in log
    assert (repo_root / "docs" / "index.html").read_text(encoding="utf-8") == "<html>v1</html>"


def test_se_sincroniza_sola_si_alguien_mas_pusheo_mientras_tanto(tmp_path):
    """Caso real de QA: Claude arreglando un bug (u otra persona) pushea al
    repo entre el momento en que esta corrida clonó/pulleó y el momento en
    que intenta publicar. Antes, el 'git push' se rechazaba
    ('rejected: fetch first') y la corrida quedaba sin publicar. Ahora
    `publicar_github_pages` se sincroniza sola antes de pushear."""
    remoto, repo_root = _preparar_remoto_y_clon()

    # Simula el push de "alguien más" (un fix de código, por ejemplo) que
    # llega al remoto DESPUÉS de que este repo_root ya se clonó, mientras
    # la corrida de acá sigue su curso.
    otro_colaborador = repo_root.parent / "otro_colaborador"
    _clonar(remoto, otro_colaborador)
    (otro_colaborador / "roi_builder_fix.txt").write_text("fix\n", encoding="utf-8")
    _git("add", "roi_builder_fix.txt", cwd=otro_colaborador)
    _git("commit", "-m", "fix: algo en el código", cwd=otro_colaborador)
    _git("push", "origin", "main", cwd=otro_colaborador)

    ruta_html = tmp_path / "ControlContenido.html"
    ruta_html.write_text("<html>v2</html>", encoding="utf-8")

    # No debe lanzar ni quedar sin publicar, a pesar del push ajeno de por medio.
    main_mod.publicar_github_pages(ruta_html, repo_root=repo_root)

    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=repo_root, check=True, capture_output=True, text=True
    ).stdout
    assert "dashboard: actualizar ControlContenido.html" in log
    assert "fix: algo en el código" in log  # el fix ajeno también llegó, via el merge automático
    assert (repo_root / "roi_builder_fix.txt").exists()  # el merge trajo el archivo del otro commit

    # Y el remoto también terminó con el commit de esta corrida (se pudo pushear).
    log_remoto = subprocess.run(
        ["git", "log", "--oneline", "main"], cwd=remoto, check=True, capture_output=True, text=True
    ).stdout
    assert "dashboard: actualizar ControlContenido.html" in log_remoto
