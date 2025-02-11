#!/bin/bash
mkdir certnotify
cp -R DEBIAN certnotify/
cp -R etc certnotify/
cp -R usr certnotify/
cp -R notification certnotify/usr/lib/certnotify/
cp *.py certnotify/usr/lib/certnotify/
chown root:root certnotify -R
chmod 755 certnotify -R
dpkg-deb --build certnotify
rm -rf certnotify