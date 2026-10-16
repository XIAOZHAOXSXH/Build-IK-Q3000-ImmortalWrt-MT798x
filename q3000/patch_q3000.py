#!/usr/bin/env python3
# Add iKuai Q3000 support to padavanonly/immortalwrt-mt798x.
# Based on https://www.right.com.cn/forum/forum.php?mod=viewthread&tid=8426542
# Run from the openwrt source root:  python3 /path/to/patch_q3000.py
import os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))

def patch(path, anchor, addition, before=False):
    s = open(path).read()
    assert anchor in s, 'anchor not found in ' + path
    if before:
        s = s.replace(anchor, addition + anchor, 1)
    else:
        s = s.replace(anchor, anchor + addition, 1)
    open(path, 'w').write(s)
    print('patched: ' + path)

def sub(path, old, new):
    s = open(path).read()
    assert old in s, 'pattern not found in ' + path
    s = s.replace(old, new, 1)
    open(path, 'w').write(s)
    print('patched: ' + path)

def main():
    # 1. Device tree
    dst = 'target/linux/mediatek/files-5.4/arch/arm64/boot/dts/mediatek/mt7981-ikuai-q3000.dts'
    shutil.copyfile(os.path.join(HERE, 'mt7981-ikuai-q3000.dts'), dst)
    print('installed: ' + dst)

    # 2. Device definition in mt7981.mk
    block = (
        'define Device/ikuai_q3000\n'
        '  DEVICE_VENDOR := iKuai\n'
        '  DEVICE_MODEL := Q3000\n'
        '  DEVICE_DTS := mt7981-ikuai-q3000\n'
        '  DEVICE_DTS_DIR := $(DTS_DIR)/mediatek\n'
        '  SUPPORTED_DEVICES := ikuai,q3000\n'
        '  UBINIZE_OPTS := -E 5\n'
        '  BLOCKSIZE := 128k\n'
        '  PAGESIZE := 2048\n'
        '  IMAGE_SIZE := 114816k\n'
        '  KERNEL_IN_UBI := 1\n'
        '  IMAGES += factory.bin\n'
        '  IMAGE/factory.bin := append-ubi | check-size $$$$(IMAGE_SIZE)\n'
        '  IMAGE/sysupgrade.bin := sysupgrade-tar | append-metadata\n'
        'endef\n'
        'TARGET_DEVICES += ikuai_q3000\n'
        '\n'
    )
    patch('target/linux/mediatek/image/mt7981.mk',
          'TARGET_DEVICES += jcg_q30\n\n', block)

    # 3. LEDs
    patch('target/linux/mediatek/mt7981/base-files/etc/board.d/01_leds',
          'h3c,nx30pro)\n'
          '\tucidef_set_led_default "green" "GREEN" "nx30pro:green" "1"\n'
          '\tucidef_set_led_default "red" "RED" "nx30pro:red" "0"\n'
          '\t;;\n',
          'ikuai,q3000)\n'
          '\tucidef_set_led_default "green" "GREEN" "q3000:green" "1"\n'
          '\tucidef_set_led_default "blue" "BLUE" "q3000:blue" "0"\n'
          '\tucidef_set_led_default "red" "RED" "q3000:red" "0"\n'
          '\t;;\n')

    # 4a. Network interfaces (lan1-3 + wan)
    patch('target/linux/mediatek/mt7981/base-files/etc/board.d/02_network',
          '\tnradio,wt9103)\n'
          '\t\tucidef_set_interfaces_lan_wan "lan1 lan2 lan3 lan4" eth1\n'
          '\t\t;;\n',
          '\tikuai,q3000)\n'
          '\t\tucidef_set_interfaces_lan_wan "lan1 lan2 lan3" wan\n'
          '\t\t;;\n')

    # 4b. MAC addresses (Factory partition offset 0x10048)
    patch('target/linux/mediatek/mt7981/base-files/etc/board.d/02_network',
          '\t*)\n'
          '\t\twan_mac=$(mtd_get_mac_binary $part_name $wan_mac_offset)\n',
          '\tikuai,q3000)\n'
          '\t\twan_mac=$(mtd_get_mac_binary $part_name 0x10048)\n'
          '\t\tlan_mac=$(macaddr_add $wan_mac 1)\n'
          '\t\t;;\n',
          before=True)

    # 5. First-boot customizations (runs once on first boot, after
    #    config_generate; only the intended values are touched)
    uci_defaults = (
        '#!/bin/sh\n'
        '# iKuai Q3000 first-boot customizations\n'
        '\n'
        '# Default LAN IP -> 192.168.6.1 (netmask left untouched)\n'
        "uci set network.lan.ipaddr='192.168.6.1'\n"
        'uci commit network\n'
        '\n'
        '# Hostname -> XZ-WRT\n'
        "uci set system.@system[0].hostname='XZ-WRT'\n"
        'uci commit system\n'
        '\n'
        '# Default LuCI theme -> argon\n'
        "uci set luci.main.mediaurlbase='/luci-static/argon'\n"
        'uci commit luci\n'
        '\n'
        'exit 0\n'
    )
    dst = 'package/base-files/files/etc/uci-defaults/99-q3000-custom'
    open(dst, 'w').write(uci_defaults)
    os.chmod(dst, 0o755)
    print('installed: ' + dst)

    # 6. Firmware version string shown in LuCI ("固件版本")
    sub('package/base-files/files/etc/openwrt_release',
        "DISTRIB_DESCRIPTION='%D %V %C'",
        "DISTRIB_DESCRIPTION='Power By 小赵先生'")

    print('ALL Q3000 PATCHES APPLIED')

if __name__ == '__main__':
    main()
