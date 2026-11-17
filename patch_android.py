import re, pathlib

root = pathlib.Path("android/app/src/main")

# 1) Landscape + no restart on rotation
mf = root / "AndroidManifest.xml"
s = mf.read_text()
if "screenOrientation" not in s:
    s = s.replace("<activity", '<activity\n            android:screenOrientation="sensorLandscape"', 1)
mf.write_text(s)

# 2) Fullscreen theme + notch support
st = root / "res/values/styles.xml"
s = st.read_text()
extra = """        <item name="android:windowFullscreen">true</item>
        <item name="android:windowLayoutInDisplayCutoutMode">shortEdges</item>
"""
s = re.sub(r'(<style name="AppTheme.NoActionBar"[^>]*>)', r'\1\n' + extra, s, count=1)
st.write_text(s)

# 3) Immersive mode (hide nav/status bars) + keep screen on
java = next(root.glob("java/**/MainActivity.java"))
pkg = re.search(r"package\s+([\w.]+);", java.read_text()).group(1)
java.write_text(f"""package {pkg};

import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {{
    @Override
    public void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        hideBars();
    }}

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {{
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideBars();
    }}

    private void hideBars() {{
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }}
}}
""")
print("patched", java)

# 4) Custom app icon (icon/ folder -> res/mipmap-*)
import shutil
res = root / "res"
icon_dir = pathlib.Path("icon")
if icon_dir.exists():
    for d in icon_dir.glob("mipmap-*"):
        dest = res / d.name
        dest.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.png"):
            shutil.copy(f, dest / f.name)
    # remove old webp icons so they don't override the PNGs
    for d in res.glob("mipmap-*"):
        for f in d.glob("ic_launcher*.webp"):
            f.unlink()
    (res / "values/ic_launcher_background.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <color name="ic_launcher_background">#000000</color>\n</resources>\n')
    print("icon applied")
