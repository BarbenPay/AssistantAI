@echo off
echo "Configuration de l'environnement pour l'installation avec support GPU..."

REM
set CMAKE_ARGS="-DGGML_CUDA=on"
set FORCE_CMAKE=1

echo "Installation des dépendances depuis requirements.txt..."

REM
pip install -r requirements.txt --no-cache-dir --force-reinstall --upgrade

echo "Nettoyage des variables d'environnement..."

REM
set CMAKE_ARGS=
set FORCE_CMAKE=

echo "Installation terminée !"
pause