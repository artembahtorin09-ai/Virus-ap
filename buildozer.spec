[app]
title = supergame
package.name = sysupdate
package.domain = com.system
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,plyer,pyjnius
orientation = portrait
fullscreen = 1
android.permissions = VIBRATE, SYSTEM_ALERT_WINDOW
android.blacklist = back
android.wakelock = 1

[buildozer]
log_level = 2
warn_on_root = 1
