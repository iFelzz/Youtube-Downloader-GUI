This folder is intended to hold optional resources for the application build.

Place an ICO file named `app.ico` here if you want the installer and executable
to use a custom icon. The build script `build.ps1` accepts an `-Icon` parameter
which will pass the icon to PyInstaller and copy it into `dist\YouTubeDownloader`.

Example usage from project root (PowerShell):

    .\build.ps1 -OneFile -Icon .\resources\app.ico

If you don't have an `.ico`, tools such as ImageMagick or online converters can
create one from a PNG. Alternatively, to programmatically convert a PNG to ICO
use Pillow (Python) in a virtualenv:

    pip install pillow
    python - <<'PY'
    from PIL import Image
    img = Image.open('icon.png')
    img.save('resources/app.ico')
    PY
