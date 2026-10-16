# iKuai Q3000 ImmortalWrt 固件自动编译

用 GitHub Actions 自动编译适用于 **iKuai Q3000**（MT7981）的
[immortalwrt-mt798x](https://github.com/padavanonly/immortalwrt-mt798x)
（`openwrt-21.02` 分支）固件。设备支持补丁参考恩山无线论坛帖子
（tid=8426542）整理。

## 固件内容

- 目标：MediaTek MT7981（`mediatek/mt7981`），设备 `ikuai_q3000`
- 端口：`lan1`、`lan2`、`lan3` 为 LAN，`wan` 为 WAN（按帖子网口顺序）
- MAC 地址：从 `Factory` 分区偏移 `0x10048` 读取，LAN 口 MAC 为 WAN 口 +1
- 三色 LED（绿/红/蓝）与复位键定义
- 内核 5.4，包含 MTK WiFi 闭源驱动（`kmod-mt_wifi`，2.4G/5G 可用）
- 硬件 NAT 驱动（`kmod-mediatek_hnat`，随 WiFi 驱动自动带入）
- LuCI 管理界面（含中文语言包）

## 出厂定制（Q3000 专属）

由 `q3000/patch_q3000.py` 在构建时注入，首次开机自动生效：

- 默认后台地址：`192.168.6.1`（掩码保持 `255.255.255.0` 不动）
- 主机名：`XZ-WRT`
- 固件版本（LuCI 状态页显示）：`Power By 小赵先生`
- 默认主题：Argon（含 `luci-app-argon-config` 设置界面）

## 使用方法

1. 在 GitHub 上新建一个仓库（名字随意，如 `q3000-firmware`）。
2. 把本仓库的全部文件（`.github/`、`q3000/`、`README.md`）复制到新仓库根目录，
   保持目录结构不变，然后 push。
3. 打开仓库页面 → **Actions** → 左侧选择
   **Build immortalwrt-mt798x for iKuai Q3000** → **Run workflow**。
4. 等待构建完成（4 核 runner 上约 1～3 小时）。
5. 构建成功后，在仓库的 **Releases** 页面下载固件：
   - `*factory.bin` —— 通过 U-Boot Web 恢复（长按复位开机，访问 `192.168.1.1`）刷机
   - `*sysupgrade.bin` —— 在 LuCI「系统 → 备份/升级」里直接升级（已刷过第三方固件时用这个）

每次点 Run workflow 都会生成一个新的 Release（tag 为 `q3000-build-<编号>`），
互不覆盖，方便对比不同版本。

## 文件说明

```
.github/workflows/build-q3000.yml   # GitHub Actions 工作流定义
q3000/mt7981-ikuai-q3000.dts         # Q3000 设备树（按论坛帖子整理）
q3000/patch_q3000.py                 # 自动补丁脚本：把设备树、设备定义、
                                     # LED、网络脚本打到源码树上
q3000/q3000-overlay.config           # 配置叠加层：Q3000 设备选择 + LuCI 中文
```

## 配置说明

工作流的配置分两步（与 [官方编译说明](https://cmi.hanwckf.top/p/immortalwrt-mt798x/)
一致）：

1. `cp -f defconfig/mt7981-ax3000.config .config` —— 采用源码自带的官方
   mt7981 配置模板，里面已经包含了正确的 WARP 驱动版本（`WARP_VERSION=2` /
   `WARP_CHIPSET="mt7981"`）、原厂 WiFi 驱动、HNAT、LuCI 等，不用自己从零拼。
2. 追加 `q3000/q3000-overlay.config` —— 只放 Q3000 相关的增量：
   设备选择（`DEVICE_ikuai_q3000`）和 LuCI 中文语言包。

## 自定义配置

想增减软件包时，编辑 `q3000/q3000-overlay.config`，按 OpenWrt `.config`
语法加行（后写的会覆盖模板里的同名项），例如：

```
CONFIG_PACKAGE_htop=y
```

然后 push，重新 Run workflow 即可。注意不要删掉文件里已有的 Q3000 设备
选择行；WARP 驱动版本等底层配置由官方模板
（`defconfig/mt7981-ax3000.config`）保证正确，不需要动。

## 常见问题

- **构建失败怎么办**：点进那次失败的 workflow run，看 **Build firmware**
  这一步的日志，末尾一般会指出是哪个包编不过。也可以把日志贴出来分析。
- **配置从哪来**：不要从零手写 `.config`。用源码自带的官方模板
  （如 mt7981 用 `defconfig/mt7981-ax3000.config`），`cp` 为 `.config`
  后再把设备相关的增量配置追加成一个 overlay 文件，最后 `make defconfig`。
  模板里已经包含了正确的驱动版本等底层配置，手写容易踩坑（实测教训：
  warp 驱动的 `WARP_VERSION`/`WARP_CHIPSET` 在 mt7981 上没有正确默认值，
  手写配置时误用了 mt7622/mt7988 的值导致整包编译失败）。
- **想固定源码版本**：默认每次都拉 `openwrt-21.02` 分支最新代码。
  如需锁定某次提交，把 workflow 里 `git clone --depth 1 -b ...` 改成先完整
  clone 再 `git checkout <commit>`。
- **Runner 换新版 Ubuntu**：工作流固定用 `ubuntu-22.04`，老版本 buildroot
  在这个镜像上验证过，不要轻易换成 `ubuntu-latest`。
