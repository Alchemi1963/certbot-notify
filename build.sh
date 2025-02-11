#!/bin/bash
mkdir certnotify
cp -R DEBIAN certnotify/
cp -R etc certnotify/
cp -R usr certnotify/
cp -R src/* certnotify/usr/lib/