---
description: Build macOS .app bundle and DMG installer (run when user says "build mac")
---

# Build macOS App + DMG

// turbo-all

1. **Run build script**

```bash
cd /Users/apple/Desktop/extension/mtips5s_veo3 && chmod +x scripts/build_mac.sh && bash scripts/build_mac.sh 2>&1
```

2. **Verify output**

```bash
ls -la /Users/apple/Desktop/extension/mtips5s_veo3/dist/Veo3DeskTop.dmg && du -sh "/Users/apple/Desktop/extension/mtips5s_veo3/dist/Whisk Desktop.app"
```

## What the script does

1. Runs 861 tests
2. Compiles universal native launcher (arm64 + x86_64)
3. Creates `.app` bundle with Info.plist, resources, themes, i18n
4. Sets `APP_ENV=prod` in launcher + bundles `.env.prod`
5. Creates DMG installer

## Output

- `dist/Whisk Desktop.app` (~2.2 MB)
- `dist/Veo3DeskTop.dmg` (~1.1 MB)
