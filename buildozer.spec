[app]
title = BlindChess
package.name = blindchess
package.domain = org.blindchess
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.include_patterns = assets/*.png
version = 1.0

requirements = python3,kivy==2.3.0,python-chess

orientation = portrait
fullscreen = 0

android.minapi = 21
android.api = 33
android.ndk = 25b
android.accept_sdk_license = True
# Letting Buildozer choose best SDK/NDK for the current environment
android.arch = arm64-v8a
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
