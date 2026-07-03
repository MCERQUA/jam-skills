---
name: thor
description: "NVIDIA Jetson AGX Thor Developer Kit handbook — hardware/ports, BSP + JetPack 7 install paths, UEFI firmware x ISO compatibility, headless install over Debug-USB, CUDA 13 / TensorRT, Docker + jetson-containers, BSP upgrades, recovery mode, troubleshooting playbook. TRIGGER on 'Thor', 'AGX Thor', 'Jetson', 'JetPack', 'L4T 38', 'tegra', 'nvpmodel', 'Blackwell devkit', NVMe flashing on Jetson, or anything about the physical Thor devkit on the bench."
---

# Jetson AGX Thor Developer Kit — Master Reference

This skill is the single-source-of-truth for our Jetson AGX Thor. Mike has the device on the bench and we have been fighting installation. Read top-to-bottom before booting it again. Every command, version, and pin reproduced below comes from NVIDIA's official `docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/` and the JetPack 7.0 release notes — no inference, no shortcuts.

> **Working assumption**: factory-shipped UEFI is `38.0.0-gcid-41245178`. If we've already pushed firmware updates onto this unit, see the **UEFI × ISO Compatibility Matrix** before flashing anything.

---

## 0. What This Thing Actually Is

Jetson AGX Thor is NVIDIA's flagship edge-AI / robotics platform. **It is not a normal Linux ARM SBC**. It boots via UEFI, ships with a custom NVIDIA L4T (Linux for Tegra) BSP on an integrated NVMe, and behaves more like a tiny SBSA server than a Pi.

| Variant | What we have |
|---|---|
| Devkit chassis | Yes — full Devkit (`945-14070-0080-000`) — module + carrier + 1 TB NVMe + 140 W USB-C PSU |
| Module | T5000 (full-fat, 128 GB) — confirm via `lsusb` recovery ID `0955:7026` (T5000) vs `0955:7226` (T4000) |

### Headline specs (T5000 / Devkit)

| Domain | Spec |
|---|---|
| AI perf | **2070 TFLOPS** FP4 (sparse) / **1035 TOPS** FP8 |
| GPU | NVIDIA **Blackwell**, 2,560 CUDA cores, 96 5th-gen Tensor Cores, 10 TPCs, MIG up to 7 partitions, 1.57 GHz |
| Compute capability | **11.0** |
| CPU | 14-core **Arm Neoverse-V3AE** 64-bit, 1 MB L2/core, 16 MB shared L3, 2.6 GHz |
| Memory | **128 GB LPDDR5X**, 256-bit bus, **273 GB/s** (NVIDIA marketing also says 276 GB/s on devkit page — same number, rounding) |
| Storage | 1 TB NVMe M.2 Key M (slot J103) pre-populated |
| Networking | 1× RJ45 **5 GbE** + 1× **QSFP28 (4× 25 GbE)** |
| Video | 2× NVENC/NVDEC |
| Vision accel | 1× PVA v3 |
| Camera | Up to 20 cameras via Holoscan Sensor Bridge / 6 via 16-lane MIPI CSI-2 / 32 via VC; C-PHY 2.1 @ 10.25 Gbps; D-PHY 2.1 @ 40 Gbps |
| Power range | **40 W – 130 W** (configurable via `nvpmodel`) |
| Power input | Micro-fit, 9–28 V DC, up to 8 A — or USB-C PD 140 W (use bundled PSU) |
| Dimensions | 243.19 × 112.40 × 56.88 mm |

vs Orin AGX: ~**7.5× higher AI compute** and **3.5× better perf/W**.

---

## 1. Hardware Layout — Cheat Sheet

### IO side (rear)
- **2× USB-A** (USB 3.2 Gen 2, 10 Gbps)
- **RJ45** Ethernet — 5 GbE
- **DisplayPort** + **HDMI**
- **USB-C port "5a"** — UFP/DFP (5 Gbps), 140 W PD sink, **Force-Recovery capable**
- **USB-C port "5b"** — same USB feature set + 140 W PD
- **QSFP28** cage — 4× 25 Gbps
- **Micro-fit DC jack** — 9–28 V / 8 A
- **Debug-USB-C** (port **8**) — behind the lid cover; this is the **serial console** at 9600 baud

### Button side (front)
- (11) **Power** — leftmost
- (12) **Force Recovery** — middle
- (13) **Reset** — right
- (14) **White status LED**

### Force-Recovery sequence
1. Hold **Force Recovery** button
2. Briefly tap **Reset** (still holding Force Recovery)
3. Release Force Recovery

Verify on host: `lsusb` shows `ID 0955:7026` (T5000) or `0955:7226` (T4000).

### Carrier
- M.2 Key M slot **J103** — 1 TB NVMe pre-installed
- Recovery-mode USB port is **J81** (per Linux_for_Tegra docs)

> The user-guide page does **not** publish a full 40-pin pinout or pinmux spreadsheet — those live in the OEM Design Guide and the AGX Thor pinmux XLS on the Jetson Download Center. If we need GPIO/I²C/SPI/UART work, pull the pinmux spreadsheet and the OEM design guide from `developer.nvidia.com/embedded/downloads`.

---

## 2. Install Paths — Which One To Use

| Path | Time | Host PC needed? | When to pick |
|---|---|---|---|
| **Jetson ISO USB** (recommended) | <15 min | No | Default for us. We have a USB stick; just flash the ISO. |
| **NVIDIA SDK Manager** | ~30 min | Ubuntu host required | When we want to pick JetPack components interactively, or pair a host PC for debugging. |
| **Linux_for_Tegra flash script** | ~30 min | Ubuntu host required | Production / scripted / CI flashing only. Required if we need a clean reflash to downgrade UEFI. |

The **Jetson ISO** path is the only one that needs no separate Ubuntu host. It also bakes Docker + nvidia-container-toolkit into the install, so we save another step.

---

## 3. Path A — Jetson ISO Install (PRIMARY)

### 3.1 What you need
- Laptop/PC (Win/Mac/Linux), **≥ 25 GB free**
- **USB stick ≥ 16 GB**
- Monitor + HDMI/DP cable + USB keyboard/mouse (or be ready for **headless** below)

### 3.2 Get the ISO
Download **Jetson ISO r38.4.0** from `developer.nvidia.com` (search "Jetson ISO" on the JetPack Download Page). r38.4.0 is the latest as of 2026-05. Older ISO r38.2 still exists but use r38.4 unless we have a reason not to (see compat matrix).

### 3.3 Burn the USB
**DO NOT** drag-copy the ISO onto the stick in Explorer/Finder. Use **balenaEtcher** (`etcher.balena.io/#download-etcher`):
1. Open Etcher → pick the ISO → pick the USB stick → Flash.

### 3.4 Boot the Thor from USB
1. Plug monitor (HDMI **or** DisplayPort), USB kbd+mouse, the bootable USB stick (any USB-A or USB-C port).
2. Power: use the **bundled 140 W USB-C PSU** into either USB-C port. *Strongly recommended* — we have seen instability with third-party PSUs.
3. Press the leftmost button (**Power**).
4. Factory UEFI boot order prioritises USB if attached — should boot the stick automatically.
5. If it doesn't: press **Esc** repeatedly at the NVIDIA splash → **Boot Manager** → make sure the USB stick is first → **Save & Exit**.

### 3.5 Flash to NVMe
At the GRUB menu on the USB stick:
1. **Flash Jetson Thor AGX Developer Kit on NVMe**
2. **Flash Jetson Thor AGX Developer Kit on NVMe 0.2.0-r38.4.0**
3. Wait ~10 min, white scrolling text is normal.
4. Auto-reboot → UEFI firmware updates → reboots **again**.
5. **REMOVE THE USB STICK NOW.** From r38.4.0 the post-install boot order still keeps the USB at the top — if you leave it in you'll boot back into the installer.

### 3.6 oem-config (first boot)
GUI walkthrough on the attached monitor: language → keyboard → NV driver EULA → Wi-Fi (or skip) → timezone → name/user/password → done. Click **Start Using Ubuntu**.

> Underlying OS is **Ubuntu 24.04 LTS**, kernel **6.8** (preemptable realtime), with the L4T overlay.

---

## 4. Path A-headless — Install Without A Monitor

If we don't have a display attached (or KVM is munging the video), use the **Debug-USB serial console** behind the lid cover (port 8). It runs at **9600 baud**.

### 4.1 Connect
USB-C cable from your laptop → the **Debug-USB** port on the Thor (NOT one of the regular USB-C ports).

Your laptop should enumerate **four** USB serial devices. The console is on the **second** one.

### 4.2 Per-OS terminal config (this is fiddly because of the UEFI 38.0.0 garbled-text bug — see §6)

**Windows / PuTTY**
- Pick the **2nd** COM port (e.g. COM4 if you got COM3-6).
- Window → Columns **244**, Rows **60** → Apply.

**macOS / Terminal**
- Font 9–10pt, resize window to **242 × 61**.
- `stty` should report `speed 9600 baud; 61 rows; 242 columns;`
- Open `/dev/cu.usbserial-0002` (or whichever is the 2nd one).

**Linux / xterm + screen**
- `stty rows 240 columns 60`
- `screen /dev/ttyACM1 115200`
- Enable line wrap.

### 4.3 Boot, hit Esc, do the install
- Press Power, press **Esc** at the pre-boot prompts to enter UEFI.
- Boot Manager → pick USB → install.

### 4.4 Headless oem-config (CUI)
After the install reboot, plug a USB cable from your laptop to a **regular USB-C port** (not Debug-USB). An **`L4T-README`** drive will mount on your laptop — that's how the Thor exposes the CUI installer. Open the serial port; navigate with **Tab** + arrow keys + Enter. Steps:

1. License → `<Ok>`
2. Language ↑↓ → `<Ok>`
3. Location ↑↓ → `<Ok>`
4. Timezone ↑↓ → `<Ok>`
5. UTC confirmation → `<Ok>`
6. Full name → `<Ok>`
7. Username → `<Ok>`
8. Password → `<Ok>`
9. Password confirm → `<Ok>` (accept weak-password warning if you go that route)
10. Network: pick **`enP2p1s0: Ethernet PCI`** → `<Ok>` (DHCP may take a moment)
11. Hostname → `<Ok>`
12. Final install, reboot, login.

---

## 5. Path B — SDK Manager (alternative)

Requires Ubuntu host. Doc: `https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html`.

Useful when:
- We want to picker-select JetPack components (TensorRT, DeepStream, etc.) instead of `apt install nvidia-jetpack`.
- We're pairing the Jetson with a host PC for combined debugging.

Step ~30 min. Same general flow: enter recovery mode (§1), connect USB, launch SDK Manager on the Ubuntu host, pick **Jetson AGX Thor Developer Kit** + JetPack 7.0, flash.

---

## 6. Path C — Linux_for_Tegra Flash Script (production / scripted)

Requires Ubuntu **22.04 or 20.04** host. Doc: `https://docs.nvidia.com/jetson/archives/r38.4/DeveloperGuide/IN/QuickStart.html`.

### 6.1 Grab BSP + rootfs
From `https://developer.nvidia.com/linux-tegra`:
- `Jetson_Linux_<version>_aarch64.tbz2`
- `Tegra_Linux_Sample-Root-Filesystem_<version>_aarch64.tbz2`

### 6.2 Prep
```bash
tar xf ${L4T_RELEASE_PACKAGE}
sudo tar xpf ${SAMPLE_FS_PACKAGE} -C Linux_for_Tegra/rootfs/
cd Linux_for_Tegra/
sudo ./tools/l4t_flash_prerequisites.sh
sudo ./apply_binaries.sh --openrm     # --openrm is Thor-specific
```

### 6.3 Put the Thor in recovery mode
1. USB-C from host to **J81** (the recovery USB-C, port 5a on the IO panel).
2. Power off.
3. Hold **Force Recovery**.
4. Tap **Power** (still holding Force Recovery).
5. Release Force Recovery.

Verify: `lsusb` shows `0955:7026` (T5000) or `0955:7226` (T4000).

### 6.4 Flash
```bash
sudo ./l4t_initrd_flash.sh jetson-agx-thor-devkit internal     # T5000 devkit (us)
# T4000 module variant:
# sudo ./l4t_initrd_flash.sh jetson-agx-thor-t4000 internal
```

### 6.5 Gotcha
The BSP **assumes NVMe ≥ 234 GiB**. Our 1 TB drive is fine. If we ever swap in a smaller one, set `EXT_NUM_SECTORS` before flashing.

---

## 7. UEFI × ISO Compatibility Matrix — READ BEFORE FLASHING AGAIN

We have hit this. The UEFI firmware on the Thor and the Jetson ISO version are coupled.

| UEFI on the unit | ISO r38.2 | ISO r38.4 |
|---|---|---|
| **r38.0.0** (factory) | OK | OK |
| **r38.2.x** | OK *(needs Display Hand-Off enabled)* | OK *(needs Display Hand-Off enabled)* |
| **r38.4.x** | ⛔ **NOT SUPPORTED** | OK |

### Implications
- If we've ever booted the box and let it auto-update firmware, we are no longer on factory 38.0.0. Check at the splash screen, or `Esc` → UEFI menu → version is shown there.
- **Once UEFI is at r38.4.x, you can ONLY install ISO r38.4.** No downgrade path through ISO — you'd have to use SDK Manager / Linux_for_Tegra to roll back.
- If UEFI is at r38.2.x, the ISO installer **WILL black-screen / fail** unless you flip **Display Hand-Off** to `Auto` first. See §8.

---

## 8. The "Black Screen On Reinstall" Trap — Display Hand-Off

**Symptom**: you already did one install of the Thor. Now you're trying to reinstall (or install a newer ISO). USB stick is fine. You boot, monitor goes black, nothing happens.

**Cause**: JetPack 7.0's GPU driver doesn't fully support display hand-off. Factory ships with `SOC Display Hand-Off Mode: Auto` so the USB installer can drive the display via efifb. The installer flips it to `Never` for normal OS operation. Once it's `Never`, you can't reinstall from USB until you flip it back.

**Fix** (must be done from the UEFI setup menu, so use headless serial if you can't see anything):

1. Power on, mash **Esc** at the NVIDIA splash.
2. **Device Manager** → **NVIDIA Configuration** → **Boot Configuration**.
3. Scroll. Find:
   - `SOC Display Hand-Off Mode` → set to **Auto**
   - `SOC Display Hand-Off Method` → set to **efifb**
4. **F10**, confirm with **y**.
5. **Esc** out, choose **Reset** from the top menu.
6. Now the USB installer can drive the display. The installer will flip Hand-Off back to `Never` automatically when it finishes — you do not need to undo this manually for future reinstalls.

> If we are seeing garbled serial console text (instead of a black screen on monitor), that's a **different** bug — the UEFI 38.0.0 garbled-text bug. See §9.

---

## 9. UEFI 38.0.0 Garbled Serial Text — Headless Bug

Factory UEFI `38.0.0-gcid-41245178` ships with a terminal-rendering bug: every char gets rendered as garbage on the Debug-USB serial console. Fixed in `38.1.0-gcid-41245178` and `38.2.0-gcid-41754123`.

Workaround until firmware is updated: force the terminal window to **242–244 columns × 60–61 rows** (per §4.2). The output is technically there, just rendering wide.

---

## 10. BSP Upgrade — r38.2.x → r38.4.x (in place, no reflash)

If we're already running Jetson Linux 38.2.x and want to move to 38.4.x without reflashing:

```bash
# 1. Verify current
cat /etc/nv_tegra_release        # expect "R38 (release), REVISION: 2.x"

# 2. Backup + retarget apt source
sudo cp /etc/apt/sources.list.d/nvidia-l4t-apt-source.list \
        /etc/apt/sources.list.d/nvidia-l4t-apt-source.list.bak
sudo sed -i 's/r38\.2/r38.4/g' /etc/apt/sources.list.d/nvidia-l4t-apt-source.list
tail -n5 /etc/apt/sources.list.d/nvidia-l4t-apt-source.list

# 3. Upgrade
sudo apt update && sudo apt upgrade -y

# 4. Reboot
sudo reboot

# 5. Confirm
cat /etc/nv_tegra_release        # expect "R38 (release), REVISION: 4.x"
```

Rollback if it goes wrong:
```bash
sudo cp /etc/apt/sources.list.d/nvidia-l4t-apt-source.list.bak \
        /etc/apt/sources.list.d/nvidia-l4t-apt-source.list
```

---

## 11. Docker + nvidia-container-toolkit

> Skip this if we installed via the Jetson ISO — Docker is already configured. Only needed after SDK Manager or Linux_for_Tegra flashes.

```bash
# Toolkit + docker
sudo apt-get update
sudo apt install -y nvidia-container curl
curl https://get.docker.com | sh && sudo systemctl --now enable docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl daemon-reload && sudo systemctl restart docker

# Make nvidia the default runtime (so `docker run` gets GPU by default)
sudo apt install -y jq
sudo jq '. + {"default-runtime": "nvidia"}' /etc/docker/daemon.json | \
    sudo tee /etc/docker/daemon.json.tmp && \
    sudo mv /etc/docker/daemon.json.tmp /etc/docker/daemon.json

# Verify
cat /etc/docker/daemon.json
# {
#   "runtimes": { "nvidia": { "args": [], "path": "nvidia-container-runtime" } },
#   "default-runtime": "nvidia"
# }

# User in docker group
sudo usermod -aG docker $USER && newgrp docker
```

### Quick GPU sanity test
```bash
docker run --rm -it -v "$PWD":/workspace -w /workspace \
  nvcr.io/nvidia/pytorch:25.08-py3
```
Inside:
```python
python3 - <<'EOF'
import torch
print("PyTorch:", torch.__version__)         # 2.8.0a0+34c6371d24.nv25.08
print("CUDA:", torch.cuda.is_available())    # True
print("GPU:", torch.cuda.get_device_name(0)) # NVIDIA Thor
x = torch.rand(10000, 10000, device="cuda")
print("sum:", x.sum().item())
EOF
```

### "permission denied … docker.sock"
Either `sudo usermod -aG docker $USER && newgrp docker`, or prefix `sudo` temporarily.

---

## 12. CUDA 13 — install paths

Three options. **Default to JetPack apt** unless you have a reason.

### A. JetPack apt (preferred on-Thor)
```bash
sudo apt update
sudo apt install nvidia-jetpack       # ~15 GB, full stack
# or, CUDA only:
sudo apt install nvidia-cuda-dev      # NOT nvidia-cuda-toolkit — that's Ubuntu's generic build
```

⚠️ **Do not `apt install nvidia-cuda-toolkit`.** It's the Ubuntu archive package, not the Jetson-tuned one. The right package is `nvidia-cuda-dev`.

### B. NGC container (no host pollution)
```bash
docker run -it --rm nvcr.io/nvidia/cuda:13.0.0-devel-ubuntu24.04
# with cuDNN:
docker run --gpus all -it --rm nvcr.io/nvidia/cuda:13.0.0-cudnn-devel-ubuntu24.04
```

### C. CUDA download page (manual)
`developer.nvidia.com/cuda-downloads` → Linux / **arm64-sbsa** / Native / **Ubuntu 24.04** / **deb (local)**. Run only the **toolkit** instructions — do **NOT** run the **Driver Installer** section that comes after; on Jetson the driver ships with L4T.

### Post-install env
```bash
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Quick verify — deviceQuery
```bash
mkdir -p $HOME/cuda-work && cd $HOME/cuda-work
docker run --rm -it -v "$PWD":/workspace -w /workspace \
  nvcr.io/nvidia/cuda:13.0.0-devel-ubuntu24.04 bash -lc '
    apt update && apt install -y --no-install-recommends git make cmake
    git clone --depth=1 --branch v13.0 https://github.com/NVIDIA/cuda-samples.git
    cd cuda-samples/Samples/1_Utilities/deviceQuery
    cmake . -DGPU_TARGETS=all -DCMAKE_BUILD_TYPE=Release
    make -j$(nproc) && ./deviceQuery
  '
```
Expected: CUDA Driver/Runtime **13.0/13.0**, device name **NVIDIA Thor**, **2560** cores, compute **11.0**, ~**125 GB** global memory.

---

## 13. JetPack 7.0 — Component Versions

JetPack 7.0 is the SDK release for AGX Thor + T5000. Versions baked in (per NVIDIA forum announcement 2025-08-25 + Jetson Linux 38.2/38.4 release notes):

| Component | Version |
|---|---|
| Jetson Linux (L4T) | 38.2 (initial) / **38.4** (current) |
| Ubuntu | **24.04 LTS** |
| Linux kernel | **6.8** (preemptable realtime) |
| CUDA | **13.0** |
| cuDNN | **9.12** |
| TensorRT | **10.13** |
| DeepStream | **7.0** |
| VPI | latest 7.x (image/vision on GPU, PVA, OFA, CPU) |
| Triton Inference Server | 24.x via NGC |
| AI serving | vLLM + SGLang NGC containers added in 7.0 |
| Holoscan Sensor Bridge | Added — CSI over Ethernet; Eagle LI-VB1940 sensor module supported |

### "What changed in JetPack 7.0 / SBSA" — practical
- Aligns Thor to **Server Base System Architecture (SBSA)** → standard ARM server boot flow (UEFI, ACPI). This is why we get a normal Ubuntu installer flow instead of the old Tegra-style tarball overlay.
- Container tag suffix `-ipgu` (Orin-era) is **no longer required** on Thor.
- Manual flashing procedures differ from Orin; you must use **`l4t_initrd_flash.sh`** not the old `flash.sh`.

---

## 14. jetson-containers + autotag — the productive container workflow

For ML/LLM/CV workloads on Thor, the community-maintained **`dusty-nv/jetson-containers`** is the fastest path. Thor + Blackwell is supported on JetPack 7.0+ (L4T R38.x).

### Install
```bash
git clone https://github.com/dusty-nv/jetson-containers
cd jetson-containers
bash install.sh         # uses sudo; adds autotag to /usr/local/bin
```

### `autotag` — pick the right tag for your JetPack
```bash
$(autotag <pkg>)        # bash command substitution expands to e.g. dustynv/pytorch:r38.4
```

### Example — run a known-good package
```bash
jetson-containers run $(autotag stable-diffusion-webui)
jetson-containers run $(autotag pytorch)
jetson-containers run $(autotag ollama)
```

### Prereqs the install script expects
- Default Docker runtime = nvidia (done in §11).
- Optional but **highly recommended on Thor**: relocate Docker data to NVMe (we have 1 TB, use it):
  ```bash
  sudo cp -r /var/lib/docker /mnt/docker
  # then edit /etc/docker/daemon.json to add "data-root": "/mnt/docker"
  sudo systemctl restart docker
  ```
- Swap (helps big builds, even with 128 GB):
  ```bash
  sudo systemctl disable nvzramconfig
  sudo fallocate -l 16G /mnt/16GB.swap
  sudo mkswap /mnt/16GB.swap
  sudo swapon /mnt/16GB.swap
  echo "/mnt/16GB.swap none swap sw 0 0" | sudo tee -a /etc/fstab
  ```

---

## 15. Power Modes / `nvpmodel`

Thor power range is **40–130 W**. NVIDIA exposes power modes via `nvpmodel`. The exact mode IDs are populated by the BSP — check live with:

```bash
sudo nvpmodel -q                    # current mode
sudo nvpmodel -p --verbose          # list modes baked in
sudo nvpmodel -m <id>               # switch
sudo jetson_clocks                  # pin clocks at max once a mode is picked
sudo jetson_clocks --show           # see current frequencies
```

Common reasons we'd touch this:
- Thermal-limited demo on a poorly-cooled bench → drop to a 40–60 W profile.
- Headroom needed for a benchmark / agent run → go max-Q at 130 W with `jetson_clocks`.

> Don't run at 130 W on the bundled USB-C PSU unless we verified PD negotiation is at 140 W. If PD dropped to 100 W, peak inference will brownout.

---

## 16. GPIO / 40-Pin / Pinmux

The user guide does **not** publish the AGX Thor 40-pin pinout. For real GPIO work:

1. Pull the **Jetson AGX Thor Pinmux** spreadsheet (XLS) from `developer.nvidia.com/embedded/downloads`.
2. Pull the **OEM Design Guide** from the same Download Center.
3. Userspace: `NVIDIA/jetson-gpio` Python library is supported. `JETGPIO` (Rubberazer) supports earlier Jetsons; verify Thor compatibility before adopting.
4. Pinmux is **statically programmed at flash time** — to change a pin's function (GPIO ↔ I²C ↔ SPI ↔ UART) you edit the pinmux XLS, regenerate `pinmux.dtsi`, and reflash. There is no `raspi-config`-style runtime switch.

Until we actually need a HAT or external sensor, we don't need to touch any of this.

---

## 17. Troubleshooting Playbook

The official troubleshooting page is "To be added." Below is the working playbook based on the install pages + JetPack 7.0 release notes + forum threads we've already burned cycles on.

| Symptom | Likely cause | Fix |
|---|---|---|
| Monitor black during install on used unit | Display Hand-Off set to `Never` after previous install | §8 — flip Hand-Off to `Auto` / efifb in UEFI |
| Garbled serial text on Debug-USB | UEFI 38.0.0 known bug | §9 — resize terminal to 242–244×60–61 cols/rows; OR upgrade UEFI to ≥38.1.0 |
| KVM gives no video to monitor | KVM can't handle Thor's display output | Plug monitor **direct** into Thor; bypass KVM |
| Boots into installer USB after install instead of NVMe | Forgot to remove USB; r38.4 keeps USB at top of UEFI boot order | Pull USB stick before reboot |
| `lsusb` shows nothing in recovery mode | Wrong recovery USB-C port, or order of buttons wrong | Use port marked recovery (J81 / 5a); hold Force-Recovery, *tap* Reset, release Force-Recovery; expect `0955:7026`/`0955:7226` |
| `apt install nvidia-jetpack` fails | Apt source still on r38.2 vs installed r38.4 (or vice versa) | `cat /etc/nv_tegra_release` and `tail /etc/apt/sources.list.d/nvidia-l4t-apt-source.list` — match them, then `apt update` |
| ISO r38.2 image hangs on UEFI 38.4.x | Unsupported combo (§7 matrix) | Use ISO r38.4 OR reflash UEFI back via SDK Manager/Linux_for_Tegra |
| Docker `permission denied … docker.sock` | User not in `docker` group | `sudo usermod -aG docker $USER && newgrp docker` |
| `nvcr.io/nvidia/pytorch:25.08-py3` CUDA unavailable | Default runtime not `nvidia` | §11 — set `default-runtime: "nvidia"` in `/etc/docker/daemon.json`, restart docker |
| `nvidia-cuda-toolkit` installed and breaking things | Wrong package — that's Ubuntu's generic, not Jetson's | Remove it, install `nvidia-cuda-dev` instead |
| Thor brownout at peak | USB-C PD dropped below 140 W | Use bundled PSU into a single USB-C; check PD with `lsusb -t` / `dmesg | grep -i pd` |
| Want to downgrade UEFI 38.4.x | No ISO downgrade path | Use SDK Manager or Linux_for_Tegra to fully reflash |
| Sub-paired / `NOT_PAIRED` errors (when we host OpenClaw or similar on Thor) | Separate from Jetson — see jambot openclaw skill | Out of scope here |

### Logs worth checking
- `/etc/nv_tegra_release` — which L4T rev we're on
- `dmesg | head -200` — boot
- `dmesg | grep -Ei 'pd|usb|nvme|tegra'` — power / NVMe / USB-C
- `journalctl -u docker` — Docker daemon
- `journalctl -b -p err` — all errors this boot
- UEFI menu → splash version — firmware version

---

## 18. Resources & Canonical URLs

Core docs (primary):
- User Guide root: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/
- Quick Start: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/quick_start.html
- BSP Setup: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/setup_bsp.html
- Docker: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/setup_docker.html
- CUDA: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/setup_cuda.html
- JetPack: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/setup_jetpack.html
- Hardware Layout: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/hardware_layout.html
- UEFI × ISO compat: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/twa_uefi_iso_compatibility.html
- Display Hand-Off workaround: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/twa_display_handoff.html
- Headless on UEFI 38.0.0: https://docs.nvidia.com/jetson/agx-thor-devkit/user-guide/latest/twa_headless_on_uefi-38-0-0.html

L4T / Developer Guide (deep):
- Linux_for_Tegra Quick Start (r38.4): https://docs.nvidia.com/jetson/archives/r38.4/DeveloperGuide/IN/QuickStart.html
- Flashing Support: https://docs.nvidia.com/jetson/archives/r38.4/DeveloperGuide/SD/FlashingSupportJetsonThor.html
- Release notes 38.2 PDF: https://docs.nvidia.com/jetson/archives/r38.2/ReleaseNotes/Jetson_Linux_Release_Notes_r38.2.pdf

Downloads:
- BSP / rootfs: https://developer.nvidia.com/linux-tegra
- JetPack: https://developer.nvidia.com/embedded/jetpack
- JetPack 7.0 archive: https://developer.nvidia.com/embedded/jetpack/downloads/archive-7.0
- Supported Components List + Pinmux + OEM Design Guide: https://developer.nvidia.com/embedded/downloads
- balenaEtcher (USB writer): https://etcher.balena.io/#download-etcher

Containers / ecosystem:
- jetson-containers: https://github.com/dusty-nv/jetson-containers
- NGC catalog: https://catalog.ngc.nvidia.com/

Community:
- Thor forum: https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/jetson-thor/
- JetPack 7.0 release thread: https://forums.developer.nvidia.com/t/jetpack-7-0-jetson-linux-38-2-for-nvidia-jetson-thor-is-now-live/343128
- Ridgerun JetPack 7.0 components wiki: https://developer.ridgerun.com/wiki/index.php/NVIDIA_Jetson_AGX_Thor/JetPack_7.0/Getting_Started/Components

Marketing / spec page:
- https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/
- https://developer.nvidia.com/embedded/jetson-agx-thor

---

## 19. House Rules When Working On The Thor

These are derived from our broader operating norms (CLAUDE.md), but they bite hard on Thor specifically:

1. **Never `rm -rf` the rootfs to "start clean".** Reflash via the documented path. We do not delete on this VPS or the Thor.
2. **Don't manually edit UEFI variables via `efibootmgr` without writing the change down here first.** Once we tip UEFI past 38.4.x there is no quick rollback.
3. **Use the bundled 140 W PSU.** Don't fight the box with a 65 W laptop charger and then blame the Thor.
4. **Reinstalls go through the Display Hand-Off ritual (§8) BEFORE booting the new USB.** Don't waste 10 min on a black screen.
5. **Keep `/etc/nv_tegra_release` in sync with the apt source `r38.x` tag.** Mismatches are how upgrades blow up.
6. **Default to the ISO path (§3).** Only drop to SDK Manager or Linux_for_Tegra when ISO can't do what we need.

---

## 20. Current Status — Mike-AI Bench

> *Living section — update this every time we touch the physical Thor.*

- **Date last updated:** 2026-05-18
- **Unit:** AGX Thor Developer Kit (T5000) — 128 GB / 1 TB NVMe
- **Bench location:** TBD (Mike to fill)
- **UEFI version on unit:** UNKNOWN — check splash next boot
- **ISO version used last:** UNKNOWN
- **Install state:** "Have been trying to get it running" (per 2026-05-18 conversation). No confirmed successful first-boot yet on file.
- **Likely next action:** Confirm UEFI version via splash or `Esc` → menu, then pick install path from §7 matrix. If we previously installed and now hit a black screen, run §8 Display Hand-Off ritual first.
- **Network plan:** RJ45 5 GbE on LAN + Tailscale to Mike-AI VPS for Hermes routing. See §22.5.
- **Intended workloads:** **OUR USE CASE: on-prem LLM inference server for JamBot, treated as "a DGX Spark sitting on the LAN."** No robotics, no cameras, no GPIO. Hermes (our LLM gateway) routes to it as another OpenAI-compatible provider. See **§22** for the full inference-server playbook.

When the box is running for the first time, log it here with:
- `cat /etc/nv_tegra_release`
- `nvidia-smi` (yes, it works on Thor — Blackwell. **`tegrastats` does NOT show GPU on Thor** — confirmed by NVIDIA staff in the FAQ thread. Use `nvidia-smi`.)
- `nvpmodel -q`
- `lsusb` / `lspci` / `ip a` snapshots

Keep this section honest. It's the only spot in this skill that should drift — everything else above is reference-grade.

---

## 21. Community Knowledge — NVIDIA Dev Forum Thor Sub-Forum (May 2026)

These are not in the official user guide. They come from `forums.developer.nvidia.com/c/.../jetson-thor/740`, including official NVIDIA staff replies (ChrisB_NV, AastaLLL, wichiu, WayneWWW). Read this before betting hours on the box.

### 21.1 OFFICIAL HARDWARE BULLETINS — pull these first

| Doc | What it is | Where |
|---|---|---|
| **Jetson Thor Series Modules Field Bulletin — QSPI Update** (Nov 19, 2025) | Official NVIDIA hardware advisory affecting Thor modules. Title implies a QSPI firmware update is required on some units. The forum thread points at a PDF on the Jetson Download Center — **download it before flashing anything**, it may impact our unit. | `developer.nvidia.com/embedded/downloads` → search "Field Bulletin" |
| **Datasheet** DS-11945-001_v1.4 (Feb 2026) | Official module datasheet | Same download center |
| **Design Guide** DG-12084-001_v1.2 (Jul 2025) | OEM Design Guide — carrier board design rules, pin lists, schematics reference | Same |
| **Supported Components List** DA-12429-001_v1.2 (Dec 2025) | The actual SCL the user-guide page points to | Same |
| **Certificate of Volatility** DA-12401-001_v1.1 (Jul 2025) | What memory holds state across power-off. Note: **clearing QSPI bricks the unit until reflash** — don't toy with it. | Same |

### 21.2 USB-C PSU — *NVIDIA official policy as of 2026-04-02*

ChrisB_NV (NVIDIA) updated the forum: **"NVIDIA Jetson Thor Developer Kit requires the USB-C power supply bundled with the kit."** Alternative PSU minimum spec:

- **5 A continuous @ 28 V**
- **7.5 A transient peak @ 28 V**

What does **NOT** work (per forum):
- UGREEN Nexode 100 W (4-port) — boots but shuts down under load
- Any 100 W PD supply — too low for Thor

What might work: ≥150 W USB-C PD supplies if they can sustain the 7.5 A @ 28 V transient. Not blessed.

For industrial/battery use we'd go via the **Micro-fit DC jack** (9–28 V / 8 A) instead of USB-C.

**Kit SKU note:** `945-14070-0087-000` ships with US/India/Thailand cords; HK needs an adapter. Our SKU is `945-14070-0080-000` — confirm what cords came in the box.

### 21.3 FAQ thread — the high-signal gotchas

These are direct quotes/paraphrases of NVIDIA staff answers on the FAQ thread (#346561):

- **`tegrastats` does NOT show GPU utilisation on Thor.** This is intentional — the SBSA dGPU driver doesn't plumb into tegrastats. **Use `nvidia-smi`** (which now works on Jetson for the first time, thanks to Thor's openrm/SBSA driver).
- **`apply_binaries.sh` must be invoked with `--openrm`** on Thor. Without it you'll see GPU errors after flash.
- **NVMe ≥ 234 GiB** is hard-required for JetPack 7.1GA flashing. Smaller drives → set `EXT_NUM_SECTORS`.
- **EEPROM "Failed to get eeprom handle for cvm" error** = I²C drive-strength too low on custom carriers. Devkit normally fine; if it ever fires on our unit, suspect cable or carrier-board damage.
- **Custom-carrier flash failure ("Parsing board information failed")** → add `SKIP_EEPROM_CHECK=1` (JetPack 7.1GA+).
- **Multimedia API moved**: old `tegra_multimedia_api` is gone. Samples now at **`/usr/src/jetson_multimedia_api/samples/`**. Encoding/decoding API surface changed because of the unified-driver (openrm) interface — old JetPack 6 code won't drop in.
- **RT kernel enablement** needs a patch to `generic_rt_build.sh`. Display-attached systems can freeze without it.

### 21.4 BPMP thermal stall after CUDA / vLLM — known kernel bug

**Thread #370477**, JetPack 7.1-b112 / L4T R38.4.0 / Kernel 6.8.12-tegra / CUDA 13.0.48 / vLLM 0.19.0.

**Symptom**: After running a large CUDA unified-memory workload (e.g. vLLM serving Qwen3.6-27B-INT4 or a `cudaMallocManaged` of ~75% of RAM with a sweeping kernel) and then *stopping it*, the BPMP thermal path stalls:

- `nvfancontrol` stuck in **D state** (uninterruptible)
- Thermal kworkers (`events_freezable_power_`) blocked in D state
- Sysfs temp reads hang
- Normal shutdown can't complete → only **hard power-off** recovers

Call stacks both go through `tegra_bpmp_transfer → __thermal_zone_get_temp`.

NVIDIA acknowledged this is similar to a known Orin lock-race bug (`host1x_intr_handle_interrupt()` vs `host1x_pollfd_poll()`). **No public fix as of 2026-05-18.** Workaround: avoid running workloads that consume >75% of unified memory until patched.

> Practical implication: if we serve LLMs via vLLM at high `--gpu-memory-utilization` (≥0.7), expect to hard-cycle the box periodically. Plan for a watchdog reset script.

### 21.5 Suspend / S2idle / wake — broken (work in progress)

**Thread #365060.** 19 replies, NVIDIA acknowledged, no fix.

Issues:
1. **PCIe-LM × DCE suspend race** — PCIe LM interrupt fires *while* DCE RM is suspending; handler reads now-clock-gated registers → AXI slave error → "Synchronous external abort." Mostly hits custom carriers; devkit is largely OK.
2. **Wake source allow-list is narrow**. USB wake works for some keyboards (ASUS K49) but not for mice or other keyboards. USB 3.2 ports P0/P1/P2 inconsistent.
3. `MODULE_SLEEP_N` may stay HIGH even after suspend — the SoC never actually slept.

**Workarounds**:
```bash
echo 0 | sudo tee /sys/power/pm_async       # disable async suspend
# Test:
sudo rtcwake -d /dev/rtc0 -m mem -s 30 -v
rtcwake --list-modes                        # freeze, mem, off, no, on, disable, show
```
Optional: `/lib/systemd/system-sleep/00-pcie-before-dce.sh` to unbind PCIe before DCE suspends. Disabling CPU idle C2 also clears it for some users.

**Recommendation for us**: don't rely on suspend/resume. Treat the Thor as always-on or fully-off.

### 21.6 Boot stall — pwm_tegra_tachometer and camera RT-mutex

**Thread #370356** (custom-board user, but the failure modes can bite the devkit if hardware shifts):

- Hang in `pwm_tegra_tachometer` probe → check `lsmod | grep pwm` and confirm fan/TACH wiring matches the Module Adaptation checklist.
- RT mutex deadlock in `tegra_camera_rtcpu` during `device_link_drop_managed` if no MIPI cameras are connected but the device tree still references `max96712_c` etc. Fix: disable the unused camera nodes in DT:
  ```dts
  &max96712_c { status = "disabled"; };
  ```

Devkit ships with sensible DT defaults, but if we ever rebuild the DT this is a trap.

### 21.7 jtop on L4T 38.4 — the right install path

`jtop` (`jetson_stats`) install **fails with hash mismatch** via stock pip on Thor / Ubuntu 24.04. Working procedure (per thread #370239):

```bash
sudo rm -rf /opt/jtop
sudo -v
curl -LsSf https://raw.githubusercontent.com/rbonghi/jetson_stats/master/scripts/upgrade-jtop.sh | bash
```

Notes:
- Even with jtop installed, it's mostly a sysstat-ish view on Thor — for **GPU** info use `nvidia-smi` (jtop's GPU panel reads from tegrastats and **tegrastats doesn't expose GPU on Thor**).
- jtop is still useful for thermal/power/clock observability.

### 21.8 vLLM on Thor — canonical install (thread #348804)

```bash
# 1. Toolkit + Python dev headers
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/sbsa/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install -y cuda-toolkit-13-0 python3-dev python3.12-dev

# 2. uv + venv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .vllm --python 3.12
source .vllm/bin/activate

# 3. Torch + vLLM (the prebuilt wheel for cu130 / aarch64 Blackwell)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
uv pip install xgrammar triton flashinfer-python --prerelease=allow
uv pip install https://github.com/vllm-project/vllm/releases/download/v0.14.0/vllm-0.14.0+cu130-cp38-abi3-manylinux_2_35_aarch64.whl

# 4. CRITICAL Blackwell env vars — set every shell that runs vLLM
export TORCH_CUDA_ARCH_LIST=11.0a              # sm_110a — without this, "sm_110a not defined" PTX error
export TRITON_PTXAS_PATH=/usr/local/cuda/bin/ptxas
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# 5. Free page cache before loading a big model
sudo sysctl -w vm.drop_caches=3
```

Then e.g. **GPT-OSS-120B (MoE)**:
```bash
mkdir -p tiktoken_encodings
wget -O tiktoken_encodings/o200k_base.tiktoken "https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken"
wget -O tiktoken_encodings/cl100k_base.tiktoken "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
export TIKTOKEN_ENCODINGS_BASE=${PWD}/tiktoken_encodings
export VLLM_USE_FLASHINFER_MXFP4_MOE=1

uv run vllm serve "openai/gpt-oss-120b" --async-scheduling --port 8000 \
  --host 0.0.0.0 --trust_remote_code --swap-space 16 --max-model-len 32000 \
  --tensor-parallel-size 1 --max-num-seqs 1024 --gpu-memory-utilization 0.7
```

**Measured perf** (forum reports):
| Model | tok/s |
|---|---|
| Qwen3-VL-32B-Instruct (dense) | ~2 |
| Qwen3-VL-30B-A3B-Instruct (MoE, 3B active) | ~27 |

> MoE > dense by ~13× on Thor at this size. Plan workloads accordingly.

### 21.9 SGLang on Thor — companion procedure (thread #348815)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .sglang --python 3.12
source .sglang/bin/activate
sudo apt install -y python3-dev python3.12-dev libnuma-dev cmake

# Same Blackwell env vars
export TORCH_CUDA_ARCH_LIST=11.0a
export TRITON_PTXAS_PATH=/usr/local/cuda/bin/ptxas
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

uv pip install sgl-kernel --prerelease=allow --index-url https://docs.sglang.ai/whl/cu130/
uv pip install sglang --prerelease=allow
uv pip install --force-reinstall torch torchvision torchaudio triton \
    --index-url https://download.pytorch.org/whl/cu130
uv pip install flashinfer-python

sudo sysctl -w vm.drop_caches=3

python3 -m sglang.launch_server \
  --model-path meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 --port 30000 \
  --mem-fraction 0.6 \
  --attention-backend triton
```

**Measured perf**: Llama-3.1-8B-Instruct decode ≈ **11 tok/s** on Thor (one user). Available GPU memory post-init ≈ 43.7 GB out of 116.85 GB.

### 21.10 Nemotron Nano Omni — the multimodal gotchas (thread #370434)

Multimodal Nemotron-Nano-Omni (text + image + audio + video) works on Thor but has fragile config:

- Use the **vLLM Docker container** path:
  ```bash
  sudo docker run -it --rm --pull always --runtime=nvidia --network host \
    vllm/vllm-openai:v0.21.0 \
    --model nvidia/NVIDIA-Nemotron-Nano-Omni \
    --max-model-len 8192 \
    --max-num-batched-tokens 4096 \
    --kv-cache-dtype fp8 \
    --gpu-memory-utilization 0.45 \
    --generation-config auto \
    --limit-mm-per-prompt '{"video":1,"image":1,"audio":1}'
  ```
- **`--generation-config auto`** is critical. `--generation-config vllm` → empty outputs / NaN logprobs.
- Install audio extras: `pip install -q 'vllm[audio]'`.
- Video: 256 frames @ 2 fps, 0.5 pruning rate.
- llama.cpp + a GGUF quant is NVIDIA's *verified* path; vLLM works but is more brittle.

### 21.11 Nemotron-3-Nano MoE — concurrency cliff (thread #370044)

Real warning if we plan to serve MoE LLMs:

- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, vLLM 0.20.2.
- At **concurrency 1** → 14.18 ms ITL, ~19 tok/s.
- At **concurrency 32** → 65.90 ms ITL, ~430 tok/s aggregate. **4.65× ITL degradation** per request.
- Dense models (Mistral-24B, Qwen-8B) only show 9–18% degradation under same load.
- **MTP speculative decoding rejected** on Nemotron-3-Nano (`NotImplementedError: Unsupported speculative method: 'mtp'`) — works on Nemotron-3-Super-120B but not Nano. NVIDIA suggested switching to `RedHatAI/Qwen3.6-35B-A3B-NVFP4` as a workaround model.
- Root cause flagged by reporter: missing Thor-specific `fused_moe` config (warning: "Using default MoE config") + sub-optimal Triton kernel tuning for sm_110 expert routing.

> Practical: don't promise MoE models to users on Thor until per-model kernels land. Dense or single-request MoE is fine.

### 21.12 Bootloader A/B slot behaviour (thread #370257)

Useful mental model for what happens if a firmware update goes sideways:

- Thor has **two bootloader slots** (A/B).
- If slot A fails to boot, slot B is **temporarily marked invalid** during its boot attempt, then re-marked valid once `cpu-bootloader` confirms it reached its stage.
- The originally-failed slot **stays invalid**.
- The "current slot is invalid" message in the flowchart is the *transient* state during a recovery boot, not a permanent failure.

Implication: if we ever see "both slots invalid" we are in genuine trouble — escalate to recovery-mode reflash, don't try to clear flags by hand.

### 21.13 Random small but useful things from the forum

- **`jtop` GPU panel is empty on Thor** — see §21.7.
- **`SKIP_EEPROM_CHECK=1`** unblocks flashing on JetPack 7.1GA if EEPROM check fails (custom carriers).
- **DisplayPort 1.4 2-lane 4K** has open issues at the moment (thread #370499) — if 4K via 2-lane DP fails, drop to 4-lane or HDMI.
- **`uinput` module is included in L4T 38.4** (confirmed in thread #370372) — virtual input devices work.
- **`mgbe1_0`** is the QSFP28 5/25 GbE interface name — useful for `ethtool` tuning.

### 21.14 Sources & follow-ups to read next

The threads we mined (open in browser if drilling deeper):
- Field Bulletins announcement: https://forums.developer.nvidia.com/t/jetson-orin-and-jetson-thor-field-bulletins/351992
- Thor Field Bulletin (QSPI): https://forums.developer.nvidia.com/t/jetson-thor-field-bulletin/352007
- USB-C PSU policy: https://forums.developer.nvidia.com/t/updated-4-2-2026-nvidia-jetson-thor-developer-kit-usb-c-power-supply/358753
- FAQ: https://forums.developer.nvidia.com/t/jetson-agx-thor-faq/346561
- BPMP thermal stall: https://forums.developer.nvidia.com/t/jetson-agx-thor-r38-4-bpmp-thermal-path-stalls-after-large-cuda-vllm-unified-memory-workload-nvfancontrol-and-thermal-kworkers-stuck-in-d-state/370477
- Suspend: https://forums.developer.nvidia.com/t/jetson-thor-suspend/365060
- Boot stall: https://forums.developer.nvidia.com/t/system-stall-when-boot-up/370356
- jtop install: https://forums.developer.nvidia.com/t/how-to-install-jtop-on-the-thor-module-when-the-l4t-version-is-38-4/370239
- vLLM canonical: https://forums.developer.nvidia.com/t/run-vllm-in-thor-from-vllm-repository/348804
- SGLang canonical: https://forums.developer.nvidia.com/t/run-sglang-in-thor/348815
- Nemotron Nano Omni: https://forums.developer.nvidia.com/t/nemotron-nano-omni-on-thor/370434
- Nemotron-3-Nano MoE concurrency: https://forums.developer.nvidia.com/t/nemotron-3-nano-on-jetson-thor-vllm-itl-degrades-4-7x-with-concurrency-mtp-rejected/370044
- Bootloader A/B: https://forums.developer.nvidia.com/t/thor-bootloader-update-failure/370257

Forum index (refresh quarterly): https://forums.developer.nvidia.com/c/robotics-edge-computing/jetson-systems/jetson-thor/740

---

## 22. Thor As JamBot's On-Prem Inference Server — THE OPERATIONAL PLAYBOOK

> **This is our actual use case.** Thor is treated like a DGX Spark sitting on the LAN: an OpenAI-compatible LLM endpoint that Hermes (our gateway) routes to as just another provider. No robots, no GPIO, no cameras.

### 22.1 What Thor Actually Is, In Our Context

| Comparison | Thor (T5000 Devkit) | NVIDIA DGX Spark (GB10) | RTX 4090 / 5090 box |
|---|---|---|---|
| Memory pool | **128 GB unified LPDDR5X** | 128 GB unified LPDDR5X | 24 / 32 GB GDDR |
| Mem bandwidth | **273 GB/s** | ~273 GB/s | 1 TB/s+ |
| AI compute (FP4 sparse) | 2,070 TFLOPS | 1,000 TFLOPS (per NVIDIA) | n/a (4090 ≈ 660 sparse FP8 TFLOPS) |
| Tensor Cores | 96 (5th gen) | ~2× Thor's | 512 (4th gen) |
| Power | 40–130 W | ~170 W | 450 W |
| Real inference (gpt-oss-120B llama.cpp tg32) | **42 tok/s** | 53 tok/s (**1.26× faster**) | doesn't fit in VRAM |
| Real inference (gpt-oss-20B tg32, batch 32) | 303 tok/s | 426 tok/s | 700+ tok/s |
| Cost | $3.5K kit | $3K kit | $1.6K + host PC |

**Key takeaway**: Spark beats Thor on prefill by **1.4–2.1×** and on decode by **1.1–1.6×** on the same llama.cpp build, despite Thor's higher paper TFLOPS. Reason: Spark has ~2× the Tensor Cores. But Thor still **runs the same 100B-class models** at usable speed — and it's what we have. For our scale (a handful of concurrent users, not a fleet) Thor is plenty.

### 22.2 Models That Fit — The 128 GB Budget

Reserve ~10–15 GB for system + KV cache headroom. Working budget: **~110 GB for the model**.

| Model | Quant | Size | Fits? | Real Thor tok/s (sources below) |
|---|---|---|---|---|
| **gpt-oss-120B** (MXFP4 MoE) | MXFP4 | 59 GB | ✅ | 42 (tg32 single) → 148 (batch 32) — JetsonHacks |
| **Qwen3-Coder-30B-A3B** (MoE) | NVFP4 | ~17 GB | ✅ | 43 (single) → 188 (batch 32) — JetsonHacks |
| **Qwen3-30B-A3B** (MoE) | NVFP4 | ~17 GB | ✅ | ~27 (vLLM) / ~218 (TRT-Edge-LLM T4000, **T5000 ≈ 237–335**) |
| **DeepSeek-R1-Distill-Qwen-32B** | FP8/INT4 | ~30 GB | ✅ | 64 (TRT-Edge-LLM T4000) |
| **Mistral-3-14B** | FP8 | ~14 GB | ✅ | 100 (TRT-Edge-LLM T4000) |
| **Nemotron-Nano-30B-A3B** (MoE) | NVFP4 | ~17 GB | ✅ | 19 single, 430 aggregate @ batch 32 — but **4.65× ITL degradation** under concurrency (§21.11) |
| **Nemotron-Nano-Omni** (multimodal) | NVFP4 | ~17 GB | ✅ | Multimodal — image/audio/video. Use `--generation-config auto` (§21.10) |
| **gpt-oss-20B** (MoE) | MXFP4 | 11 GB | ✅ | 57 (single) → 303 (batch 32) |
| **Qwen2.5-Coder-7B** | Q8 | 7.5 GB | ✅ | 25 (single) → 341 (batch 32) |
| **Gemma 3 4B QAT** | Q4 | 2.4 GB | ✅ | 67 (single) → 447 (batch 32) |
| **Llama 3.1-8B-Instruct** | FP16 | ~16 GB | ✅ | 11 (SGLang decode) |
| **Llama 3.3-70B** (dense) | INT4 | ~40 GB | ✅ | slow (~5–10 tok/s estimated; dense ≫ MoE penalty) |

**Heuristic**: prefer **MoE in NVFP4/MXFP4** over dense FP16/INT4. Thor is **memory-bandwidth-bound** for inference — fewer activated params per token = much higher tok/s. MoE wins by 5–13× over dense at the same parameter count.

### 22.3 Inference Stack Picker

Five viable stacks on Thor. Pick by feature, not vibe.

| Stack | OpenAI API | Best for | Setup pain | Notes |
|---|---|---|---|---|
| **Ollama (container)** | ✅ (native `/v1/chat/completions`) | Fast start, model library, single user | ⭐ trivial | Native installer doesn't support Thor yet — use the NV-IoT container. Underneath: llama.cpp (≈ half peak perf). |
| **vLLM** | ✅ (`vllm serve`) | Production multi-user, MoE, FP8/NVFP4 | ⭐⭐ moderate | Fastest mainstream OSS path. Forum-canonical install (§21.8). |
| **SGLang** | ✅ (`sglang launch_server`) | Long-context, complex sampling, function calling | ⭐⭐ moderate | Alternative to vLLM (§21.9). |
| **TensorRT Edge-LLM** | ❌ | Absolute lowest latency, custom integrations | ⭐⭐⭐⭐ heavy | NVIDIA's blessed path on 7.1. C++ runtime, NVFP4. No OpenAI server — wrap yourself if needed. |
| **Triton Inference Server** | partial | Multi-model serving, heterogeneous backends | ⭐⭐⭐ heavy | NGC `-igpu` tag. Right when serving >1 model with different framework needs. |

**Our recommended default: vLLM.** Best balance of perf, OpenAI compat (Hermes plugs in zero-friction), and active community. Fall back to Ollama for one-off quick tests.

### 22.4 The Stand-Up Procedure (idempotent)

Assumes the box is flashed, on the network, and you're SSH'd in as a sudoer.

```bash
# A. Confirm GPU works (this is the canonical "is everything OK" check)
nvidia-smi                                       # NOT tegrastats — §21.3
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

# B. Pick a power profile for sustained inference. 130W needs the bundled PSU.
sudo nvpmodel -q
sudo nvpmodel -m <max-mode-id>                   # whichever ID maps to 130W
sudo jetson_clocks                               # pin clocks high
sudo jetson_clocks --show

# C. Disable the page cache between model loads (recommended in forum)
echo 'vm.drop_caches=3' | sudo tee -a /etc/sysctl.d/99-thor-inference.conf

# D. Move Docker data to NVMe (we have 1 TB, model weights are big)
sudo systemctl stop docker
sudo rsync -a /var/lib/docker/ /mnt/docker/
sudo jq '. + {"data-root": "/mnt/docker"}' /etc/docker/daemon.json | \
  sudo tee /etc/docker/daemon.json.tmp && sudo mv /etc/docker/daemon.json.tmp /etc/docker/daemon.json
sudo systemctl start docker

# E. Pre-pull our default inference image (vLLM canonical wheel build runs in venv, so
#    we use the vllm/vllm-openai container for the prod serving path)
sudo docker pull vllm/vllm-openai:v0.21.0

# F. Install jtop the special way (§21.7) — for thermal/power monitoring
sudo rm -rf /opt/jtop
curl -LsSf https://raw.githubusercontent.com/rbonghi/jetson_stats/master/scripts/upgrade-jtop.sh | bash
```

### 22.5 Network exposure — JamBot wiring

Mike-AI VPS is in Hetzner Ashburn. Thor sits on a residential LAN. Bridge the two with **Tailscale** (one Tailnet, two nodes). No public ports opened.

```bash
# On Thor:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
tailscale ip -4                                  # note this IP — e.g. 100.x.y.z
```

```bash
# On Mike-AI VPS (already in our Tailnet? confirm):
tailscale status | grep thor                     # should list the new node
curl http://100.x.y.z:8000/v1/models             # smoke once vLLM is up
```

**Why Tailscale and not WireGuard from scratch**: zero firewall config, MagicDNS gives us `thor.<tailnet>.ts.net`, MTU is auto, ACLs are JSON.

**Why not Cloudflare Tunnel**: latency for streaming completions matters. Tailscale stays on the direct path when both nodes are reachable.

### 22.6 Bringing up vLLM as a serving daemon

The forum-canonical install (§21.8) uses uv in a venv. For a **persistent server** prefer the container path:

```bash
# Pull a model into a host-mounted HF cache
mkdir -p /mnt/hf-cache
sudo docker run --rm --runtime=nvidia \
  -v /mnt/hf-cache:/root/.cache/huggingface \
  -e HF_TOKEN="$HF_TOKEN" \
  vllm/vllm-openai:v0.21.0 \
  python -c "from huggingface_hub import snapshot_download; \
             snapshot_download('openai/gpt-oss-120b')"

# Serve gpt-oss-120B (MoE) at port 8000, accessible on Tailnet only
sudo docker run -d --restart=unless-stopped \
  --name vllm-thor \
  --runtime=nvidia \
  -p 8000:8000 \
  -v /mnt/hf-cache:/root/.cache/huggingface \
  -e VLLM_USE_FLASHINFER_MXFP4_MOE=1 \
  -e TORCH_CUDA_ARCH_LIST=11.0a \
  vllm/vllm-openai:v0.21.0 \
  --model openai/gpt-oss-120b \
  --host 0.0.0.0 --port 8000 \
  --max-model-len 32000 \
  --gpu-memory-utilization 0.65 \           # 0.65 not 0.85 — §21.4 thermal stall risk
  --max-num-seqs 64 \
  --trust-remote-code
```

**Critical knobs:**
- `--gpu-memory-utilization 0.65` — staying below 0.7 reduces the BPMP thermal-stall hazard (§21.4) where `nvfancontrol` jams after big workloads.
- `--max-num-seqs 64` — Thor's MoE concurrency cliff hits hard above ~32 (§21.11). If we see ITL degrade, drop to 32.
- `-p 8000:8000` — bind to 0.0.0.0 inside the container; outside the container the Tailscale interface gates access.

**Smoke from Mike-AI VPS:**
```bash
curl -s http://thor.<tailnet>.ts.net:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"openai/gpt-oss-120b","messages":[{"role":"user","content":"ping"}],"max_tokens":32}'
```

### 22.7 Hermes integration

Hermes (our LLM gateway, see memory `[[hermes-agent]]`, `[[hermes-midflight-pipeline]]`) routes by subscription tier. Adding Thor is a provider entry, not a code change.

Pattern (subject to confirmation against current Hermes config schema):
```yaml
# jambot/hermes/config.yaml — pseudo, confirm against live schema
providers:
  thor:
    kind: openai
    base_url: http://thor.<tailnet>.ts.net:8000/v1
    models:
      - openai/gpt-oss-120b
      - Qwen/Qwen3-Coder-30B-A3B
    api_key: not-required-on-tailnet
    weight: high                         # prefer over Z.AI for matched models
    timeout_ms: 60000
    streaming: true
```

Behavioural notes for the routing layer:
- **Always-on**: Thor is 24/7 power-on. No cold-start handling needed beyond a normal HTTP retry.
- **Failure mode**: if Thor returns 5xx or times out, fall back to Z.AI/MiniMax (our current primary stack — `[[glm-primary-temporary-swap]]`).
- **Cost shape**: Thor is sunk-cost — there's no per-token charge. Hermes routing should *prefer* Thor for models it actually serves, then degrade to paid APIs.

### 22.8 Multi-tenancy via MIG — NOT YET

Thor hardware supports MIG (10 TPCs, up to 7 instances). **JetPack 7.0 GA does NOT implement MIG software** (§21 thread #344978 — NVIDIA staff confirmed "planned, will update"). All standard `nvidia-smi mig` commands fail with "Insufficient Resources" or "No GPU instances found."

**Implication for JamBot multi-tenant**: until MIG ships, Thor serves **one shared inference pool**. Per-tenant isolation is HTTP-layer only (Hermes auth + rate limit). When MIG GA's lands, revisit: slice into e.g. 2× 60 GB instances → run gpt-oss-120B and a smaller VLM concurrently with hardware isolation.

**Workaround today**: run **multiple vLLM containers**, each with `CUDA_MPS_PIPE_DIRECTORY` (CUDA Multi-Process Service) sharing the single GPU. Not isolated — concurrent loads will fight — but it's the only multi-model option on 7.0 GA. Pin different `--port` per container.

### 22.9 Power, thermal, sustained-inference reality

- **Bundled 140 W PSU is mandatory** (§21.2). Without it, 130 W mode will brownout under sustained MoE inference.
- **Monitor**: `jtop` for temperature/clocks, `nvidia-smi -l 5` for GPU util/power.
- **Thermal-stall watchdog**: until §21.4 is patched, a sustained workload at >75% mem util can lock `nvfancontrol`. Recommended watchdog:
  ```bash
  # /usr/local/bin/thor-thermal-watchdog.sh
  while true; do
    if ! timeout 5 cat /sys/class/thermal/thermal_zone0/temp >/dev/null; then
      logger -t thor-watchdog "thermal sysfs hung — hard reboot"
      sudo systemctl reboot --force --force
    fi
    sleep 30
  done
  ```
  Run as systemd unit on Thor. Yes, hard reboot — soft `reboot` will hang too once BPMP is locked.
- **Sustained 130 W is fine** thermally on the devkit (NVIDIA spec'd). Just don't expect to do it on a 100 W charger.

### 22.10 What we should *not* run on Thor (yet)

- ❌ Training / fine-tuning of >7B models — Thor is inference-tuned, bandwidth-limited. Use a real H100 / cloud GPU for training, ship the checkpoint to Thor for serving.
- ❌ Multi-tenant *isolated* inference — wait for MIG GA.
- ❌ Anything that needs >32K context on dense models — decode degrades sharply (gpt-oss-120B drops from 42 to 32 tok/s at 32K).
- ❌ MTP speculative decoding on Nemotron-3-Nano — rejected (§21.11). Speculative decode on Nemotron-3-Super-120B works.
- ❌ Suspend/resume in serving loop — broken (§21.5). Treat the box as always-on.

### 22.11 What's officially blessed on JetPack 7.1 (per NVIDIA blog)

Models NVIDIA published benchmarks for on T4000 (T5000 ≈ 65–92% higher):
- Qwen3-30B-A3B — 218 tok/s
- Qwen 3 32B — 68 tok/s
- Nemotron 12B — 40 tok/s
- DeepSeek R1 Distill Qwen 32B — 64 tok/s
- Mistral 3 14B — 100 tok/s
- GR00T N1.5 (robotics policy, irrelevant for us) — 376 tok/s
- Kokoro TTS — 1,100 tok/s

**Kokoro TTS at 1,100 tok/s** is interesting — if Hermes ever wants to do on-prem TTS instead of Supertonic/Groq, Thor can absolutely host it. (Memory: `[[feedback_never_use_groq_for_llm]]` — Groq=TTS-only on our stack; Thor could replace that line item entirely.)

### 22.12 Quick-reference cheat sheet

```bash
# Status
nvidia-smi                                  # GPU view (tegrastats does NOT show GPU on Thor!)
jtop                                        # CPU/mem/thermal/power (GPU pane will be empty)
sudo nvpmodel -q                            # current power mode
docker logs -f vllm-thor                    # serving daemon logs

# Restart serving
sudo docker restart vllm-thor

# Swap to different model (gpt-oss-20B for faster responses, or 120B for quality)
sudo docker stop vllm-thor && sudo docker rm vllm-thor
# ... re-run §22.6 docker run with new --model arg

# Drop page cache before big model load
sudo sysctl -w vm.drop_caches=3

# From Mike-AI VPS — verify Thor is reachable on Tailnet
curl -s http://thor.<tailnet>.ts.net:8000/v1/models | jq

# In emergency — thermal stall recovery (§22.9)
sudo systemctl reboot --force --force
```

### 22.13 Sources

- JetsonHacks Spark-vs-Thor llama.cpp benchmarks (the real numbers): https://jetsonhacks.com/wp-content/uploads/2025/10/SparkThorLlamaBenchmarks.html
- JetsonHacks article: https://jetsonhacks.com/2025/10/31/nvidia-jetson-agx-thor-vs-dgx-spark-benchmarks/
- Jetson AI Lab — Ollama on Jetson: https://www.jetson-ai-lab.com/tutorials/ollama/
- Jetson AI Lab — TensorRT Edge-LLM: https://www.jetson-ai-lab.com/tutorials/tensorrt-edge-llm/
- NVIDIA TensorRT-Edge-LLM repo: https://github.com/NVIDIA/TensorRT-Edge-LLM
- NVIDIA JetPack 7.1 blog (inference improvements + T4000 numbers): https://developer.nvidia.com/blog/accelerate-ai-inference-for-edge-and-robotics-with-nvidia-jetson-t4000-and-nvidia-jetpack-7-1/
- Antmicro Kenning benchmarks on Thor: https://antmicro.com/blog/2025/12/testing-ai-models-on-jetson-thor-with-kenning
- MIG-on-Thor forum (not-supported confirmation): https://forums.developer.nvidia.com/t/how-to-use-mig-technology-to-divide-computing-units-in-thor/344978
- vLLM canonical install on Thor (forum): https://forums.developer.nvidia.com/t/run-vllm-in-thor-from-vllm-repository/348804
- SGLang canonical install on Thor (forum): https://forums.developer.nvidia.com/t/run-sglang-in-thor/348815
- Tailscale + Ollama remote-access pattern: https://logarithmicspirals.com/blog/using-tailscale-to-access-private-llms/
