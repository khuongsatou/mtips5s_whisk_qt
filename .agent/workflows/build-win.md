---
description: Build Windows .exe via SSH + Docker (run when user says "build win" or "build exe")
---

# Build Windows EXE

Server: `root@45.32.63.217` (password: `m[Z3T(r%ghDWpk.q`)
Docker image: `tobix/pywine` with PyInstaller

// turbo-all

1. **Sync project to server**

```bash
sshpass -p 'm[Z3T(r%ghDWpk.q' rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='dist' --exclude='dist-win' --exclude='build' --exclude='node_modules' --exclude='.git' --exclude='pucaptcha/node_modules' -e 'ssh -o StrictHostKeyChecking=no' /Users/apple/Desktop/extension/mtips5s_veo3/ root@45.32.63.217:/root/mtips5s_veo3/ 2>&1 | tail -5
```

2. **Docker build on server**

```bash
sshpass -p 'm[Z3T(r%ghDWpk.q' ssh -o StrictHostKeyChecking=no root@45.32.63.217 'cd /root/mtips5s_veo3 && docker build -f Dockerfile.win -t veo3-win-build . 2>&1' | tail -20
```

3. **Extract .exe from container**

```bash
sshpass -p 'm[Z3T(r%ghDWpk.q' ssh -o StrictHostKeyChecking=no root@45.32.63.217 'docker rm -f veo3-win-extract 2>/dev/null; docker create --name veo3-win-extract veo3-win-build && rm -rf /root/mtips5s_veo3/dist-win && mkdir -p /root/mtips5s_veo3/dist-win && docker cp veo3-win-extract:/app/dist/Veo3DeskTop /root/mtips5s_veo3/dist-win/ && docker rm veo3-win-extract && du -sh /root/mtips5s_veo3/dist-win/Veo3DeskTop/'
```

4. **Download .exe to Mac**

```bash
rm -rf /Users/apple/Desktop/extension/mtips5s_veo3/dist-win && mkdir -p /Users/apple/Desktop/extension/mtips5s_veo3/dist-win && sshpass -p 'm[Z3T(r%ghDWpk.q' scp -o StrictHostKeyChecking=no -r root@45.32.63.217:/root/mtips5s_veo3/dist-win/Veo3DeskTop /Users/apple/Desktop/extension/mtips5s_veo3/dist-win/
```

5. **Verify output**

```bash
ls -la /Users/apple/Desktop/extension/mtips5s_veo3/dist-win/Veo3DeskTop/Veo3DeskTop.exe && du -sh /Users/apple/Desktop/extension/mtips5s_veo3/dist-win/Veo3DeskTop/
```

## Output

- `dist-win/Veo3DeskTop/Veo3DeskTop.exe` (~2.6 MB)
- `dist-win/Veo3DeskTop/` total (~43 MB, includes `_internal/`)
- `APP_ENV=prod` + `.env.prod` bundled

## Distribution

Zip the entire `dist-win/Veo3DeskTop/` folder for Windows users.
