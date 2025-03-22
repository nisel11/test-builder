#!/usr/bin/env bash
set -o pipefail

{ command -v /usr/sbin/efibootmgr && /usr/sbin/efibootmgr || command -v /usr/bin/efibootmgr && /usr/bin/efibootmgr; } > /dev/null 2>&1
TYPE_BOOT=${TYPE_BOOT:-$( [ $? -eq 0 ] && echo "UEFI" || echo "LEGACY" )}

quit_on_err() { echo "ERROR: $1" >&2; exit 1; }

check_commands() {
    local cmds=(wipefs parted lsblk sfdisk blkid cryptsetup blockdev mkfs.vfat mkfs.ext4 mkfs.btrfs btrfs podman rsync)
    for cmd in "${cmds[@]}"; do
        sudo which "$cmd" >/dev/null 2>&1 || quit_on_err "Команда '$cmd' не найдена. Установите её и повторите попытку."
    done
}

prepare_disk() {
    if [[ $OSI_DEVICE_IS_PARTITION -eq 0 ]]; then
        echo "Подготовка полного диска: $OSI_DEVICE_PATH"
        sudo wipefs --all "$OSI_DEVICE_PATH" || quit_on_err "Ошибка вайпа диска"
        sudo parted -s "$OSI_DEVICE_PATH" mklabel gpt || quit_on_err "Ошибка создания GPT метки"

        if [[ "$TYPE_BOOT" == "LEGACY" ]]; then
            sudo parted -s "$OSI_DEVICE_PATH" mkpart primary ext4 1MiB 3MiB || quit_on_err "Ошибка создания BIOS Boot раздела"
            sudo parted -s "$OSI_DEVICE_PATH" set 1 bios_grub on || quit_on_err "Ошибка установки флага bios_grub"
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-efi fat32 3MiB 1003MiB || quit_on_err "Ошибка создания EFI раздела"
            sudo parted -s "$OSI_DEVICE_PATH" set 2 boot on || quit_on_err "Ошибка установки boot флага для EFI"
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-boot ext4 1003MiB 3003MiB || quit_on_err "Ошибка создания Boot раздела"
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-root "$ROOT_FS" 3003MiB 25003MiB || quit_on_err "Ошибка создания Root раздела"
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-temp ext4 25003MiB 60003MiB || quit_on_err "Ошибка создания Temp раздела"
        else
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-efi fat32 1MiB 601MiB || quit_on_err "Ошибка создания EFI раздела"
            sudo parted -s "$OSI_DEVICE_PATH" set 1 boot on || quit_on_err "Ошибка установки boot флага для EFI"
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-boot ext4 601MiB 2601MiB || quit_on_err "Ошибка создания Boot раздела"
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-root "$ROOT_FS" 2601MiB 25001MiB || quit_on_err "Ошибка создания Root раздела"
            sudo parted -s "$OSI_DEVICE_PATH" mkpart alt-temp ext4 25001MiB 60001MiB || quit_on_err "Ошибка создания Temp раздела"
        fi
    else
        DISK="/dev/$(sudo lsblk -no pkname "$OSI_DEVICE_PATH" 2>/dev/null)"
        PART_NUM=$(echo "$OSI_DEVICE_PATH" | grep -o '[0-9]\+$')
        [[ -z "$PART_NUM" ]] && quit_on_err "Не удалось извлечь номер раздела"
        PART_INFO=$(sudo sfdisk -d "$DISK" | grep "^$OSI_DEVICE_PATH") || quit_on_err "Информация о разделе не найдена"
        START=$(echo "$PART_INFO" | awk -F'start=' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
        SIZE=$(echo "$PART_INFO" | awk -F'size=' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
        [[ -z "$START" || -z "$SIZE" ]] && quit_on_err "Ошибка получения данных о разделе"

        EFI_SIZE=$((600 * 1024 * 1024))
        BOOT_SIZE=$((2 * 1024 * 1024 * 1024))
        ROOT_SIZE=$((19 * 1024 * 1024 * 1024))
        TEMP_SIZE=$((35 * 1024 * 1024 * 1024))
        if [[ "$TYPE_BOOT" == "LEGACY" ]]; then
            BIOS_SIZE=$((2 * 1024 * 1024))
        else
            BIOS_SIZE=0
        fi

        SECSIZE=$(sudo blockdev --getss "$DISK") || quit_on_err "Не удалось определить размер сектора"
        BIOS_SEC=$(( (BIOS_SIZE + SECSIZE - 1) / SECSIZE ))
        EFI_SEC=$(( (EFI_SIZE + SECSIZE - 1) / SECSIZE ))
        BOOT_SEC=$(( (BOOT_SIZE + SECSIZE - 1) / SECSIZE ))
        ROOT_SEC=$(( (ROOT_SIZE + SECSIZE - 1) / SECSIZE ))
        TEMP_SEC=$(( (TEMP_SIZE + SECSIZE - 1) / SECSIZE ))
        TOTAL=$(( BIOS_SEC + EFI_SEC + BOOT_SEC + ROOT_SEC + TEMP_SEC ))
        (( TOTAL > SIZE )) && quit_on_err "Недостаточно места"

        sudo sfdisk --delete "$DISK" "$PART_NUM" || quit_on_err "Не удалось удалить раздел $PART_NUM"
        if [[ "$TYPE_BOOT" == "LEGACY" ]]; then
            P1="$PART_NUM"; P2=$(( PART_NUM+1 )); P3=$(( PART_NUM+2 )); P4=$(( PART_NUM+3 )); P5=$(( PART_NUM+4 ))
            S1=$START; E1=$(( S1+BIOS_SEC-1 ))
            S2=$(( E1+1 )); E2=$(( S2+EFI_SEC-1 ))
            S3=$(( E2+1 )); E3=$(( S3+BOOT_SEC-1 ))
            S4=$(( E3+1 )); E4=$(( S4+ROOT_SEC-1 ))
            S5=$(( E4+1 )); E5=$(( S5+TEMP_SEC-1 ))
            (( E5 > START+SIZE )) && quit_on_err "Новый раздел выходит за пределы исходного"
            sudo parted -s "$DISK" unit s mkpart alt-bios ${S1} ${E1}
            sudo parted -s "$DISK" set "$P1" bios_grub on || quit_on_err "Ошибка установки флага bios_grub"
            sudo parted -s "$DISK" unit s mkpart alt-efi ${S2} ${E2}
            sudo parted -s "$DISK" set "$P2" boot on || quit_on_err "Ошибка установки флага boot"
            sudo parted -s "$DISK" unit s mkpart alt-boot ${S3} ${E3}
            sudo parted -s "$DISK" unit s mkpart alt-root ${S4} ${E4}
            sudo parted -s "$DISK" unit s mkpart alt-temp ${S5} ${E5}
        else
            P1="$PART_NUM"; P2=$(( PART_NUM+1 )); P3=$(( PART_NUM+2 )); P4=$(( PART_NUM+3 ))
            S1=$START; E1=$(( S1+EFI_SEC-1 ))
            S2=$(( E1+1 )); E2=$(( S2+BOOT_SEC-1 ))
            S3=$(( E2+1 )); E3=$(( S3+ROOT_SEC-1 ))
            S4=$(( E3+1 )); E4=$(( S4+TEMP_SEC-1 ))
            (( E4 > START+SIZE )) && quit_on_err "Новый раздел выходит за пределы исходного"
            sudo parted -s "$DISK" unit s mkpart alt-efi ${S1} ${E1}
            sudo parted -s "$DISK" set "$P1" boot on || quit_on_err "Ошибка установки флага boot"
            sudo parted -s "$DISK" unit s mkpart alt-boot ${S2} ${E2}
            sudo parted -s "$DISK" unit s mkpart alt-root ${S3} ${E3}
            sudo parted -s "$DISK" unit s mkpart alt-temp ${S4} ${E4}
        fi

        sudo partprobe "$DISK" || sleep 2
    fi

    # Export partition variables
    export EFI_PART=$(sudo blkid -o device -t PARTLABEL=alt-efi) || quit_on_err "EFI раздел не найден"
    export BOOT_PART=$(sudo blkid -o device -t PARTLABEL=alt-boot) || quit_on_err "Boot раздел не найден"
    export ROOT_PART=$(sudo blkid -o device -t PARTLABEL=alt-root) || quit_on_err "Не найден Root раздел"
    export TEMP_PART=$(sudo blkid -o device -t PARTLABEL=alt-temp) || quit_on_err "Не найден Temp раздел"

    encrypt_root
}

format_and_create_subvolumes() {
    sudo mkfs.vfat -F32 "$EFI_PART" || quit_on_err "Ошибка форматирования EFI"
    sudo mkfs.ext4 -F "$BOOT_PART" || quit_on_err "Ошибка форматирования Boot"
    sudo mkfs.btrfs -f "$ROOT_PART" || quit_on_err "Ошибка форматирования Root (btrfs)"
    sudo mkfs.ext4 -F "$TEMP_PART" || quit_on_err "Ошибка форматирования Temp"

    sudo mkdir -p "/mnt/btrfs-setup" || quit_on_err "Ошибка создания точки монтирования"
    sudo mount -o rw,subvol=/ "$ROOT_PART" "/mnt/btrfs-setup" || quit_on_err "Ошибка монтирования btrfs раздела"
    sudo btrfs subvolume create "/mnt/btrfs-setup/@" || quit_on_err "Ошибка создания подтома @"
    sudo btrfs subvolume create "/mnt/btrfs-setup/@home" || quit_on_err "Ошибка создания подтома @home"
    sudo btrfs subvolume create "/mnt/btrfs-setup/@var" || quit_on_err "Ошибка создания подтома @var"
    sudo umount "/mnt/btrfs-setup"
}

mount_partitions() {
    sudo mount --mkdir -o subvol=@ "$ROOT_PART" "/mnt/target" || quit_on_err "Ошибка монтирования подтома @"
    sudo mount --mkdir "$BOOT_PART" "/mnt/target/boot" || quit_on_err "Ошибка монтирования Boot"
    sudo mount --mkdir "$EFI_PART" "/mnt/target/boot/efi" || quit_on_err "Ошибка монтирования EFI"
    sudo mount --mkdir "$TEMP_PART" "/var/lib/containers" || quit_on_err "Ошибка монтирования Temp"
}

install_system() {
    UUID_BOOT=$(sudo blkid -s UUID -o value "$BOOT_PART") || quit_on_err "Не удалось получить UUID boot"
    [[ $OSI_USE_ENCRYPTION -eq 0 ]] && export RAW_ROOT=$(sudo blkid -o device -t PARTLABEL=alt-root)
    UUID_ROOT=$(sudo blkid -s UUID -o value "$RAW_ROOT") || quit_on_err "Не удалось получить UUID root"

    BOOTC_CMD="bootc install to-filesystem --skip-fetch-check --disable-selinux "
    [[ "$TYPE_BOOT" != "UEFI" ]] && BOOTC_CMD+=" --generic-image "
    [[ "$OSI_USE_ENCRYPTION" -eq 1 ]] && BOOTC_CMD+=" --boot-mount-spec=\"UUID=$UUID_BOOT\" --root-mount-spec=\"/dev/mapper/alt-root\" --karg=\"rd.luks.name=$UUID_ROOT=alt-root rootflags=subvol=@\" "

    sudo podman run --rm --privileged --pid=host \
        -v "/var/lib/containers":"/var/lib/containers" \
        -v /dev:/dev \
        -v "/mnt/target":"/mnt/target" \
        ghcr.io/alt-gnome/alt-atomic:latest \
        sh -c "\
            [ -f /usr/libexec/init-ostree.sh ] && /usr/libexec/init-ostree.sh; \
            $BOOTC_CMD /mnt/target" || quit_on_err "Ошибка установки системы"
}

cleanup_temp_and_resize_root() {
    umount_all
    umount_all

    if [[ "$TEMP_PART" == *"/dev/nvme"* ]]; then
        disk="${TEMP_PART%%p*}"
        part_number="${TEMP_PART##*p}"
    else
        disk="${TEMP_PART%[0-9]*}"
        part_number="${TEMP_PART#$disk}"
    fi
    sudo parted -s "$disk" rm "$part_number" || quit_on_err "Ошибка удаления temp раздела"
    
    if [[ "$RAW_ROOT" == *"/dev/nvme"* ]]; then
        root_disk="${RAW_ROOT%%p*}"
        root_number="${RAW_ROOT##*p}"
    else
        root_disk="${RAW_ROOT%[0-9]*}"
        root_number="${RAW_ROOT#$root_disk}"
    fi
    sudo parted -s "$disk" resizepart "$root_number" 100% || quit_on_err "Ошибка изменения размера root раздела"
    
    if [[ "$OSI_USE_ENCRYPTION" -eq 1 ]]; then
        echo "${OSI_ENCRYPTION_PIN}" | sudo cryptsetup resize alt-root || quit_on_err "Ошибка обновления размера LUKS контейнера"
    fi

    sudo mount --mkdir "$ROOT_PART" "/mnt/btrfs-root" || quit_on_err "Ошибка монтирования для расширения btrfs"
    sudo btrfs filesystem resize max "/mnt/btrfs-root" || quit_on_err "Ошибка расширения btrfs"
    sudo umount "/mnt/btrfs-root"
}

encrypt_root() {
    if [[ "$OSI_USE_ENCRYPTION" -eq 1 ]]; then
        export RAW_ROOT=$(sudo blkid -o device -t PARTLABEL=alt-root)
        [[ -z "$RAW_ROOT" ]] && quit_on_err "Root раздел не найден"
        echo "${OSI_ENCRYPTION_PIN}" | sudo cryptsetup --force-password -q luksFormat "$RAW_ROOT" || quit_on_err "Ошибка шифрования root раздела"
        echo "${OSI_ENCRYPTION_PIN}" | sudo cryptsetup open "$RAW_ROOT" alt-root || quit_on_err "Ошибка открытия зашифрованного раздела"
        export ROOT_PART="/dev/mapper/alt-root"
    fi
}

umount_all() {
    sudo umount "/mnt/target/boot/efi" 2>/dev/null
    sudo umount "/mnt/target/boot" 2>/dev/null
    sudo umount "/mnt/target" 2>/dev/null
    sudo umount "/mnt/btrfs/var" 2>/dev/null
    sudo umount "/mnt/btrfs/home" 2>/dev/null
    sudo umount "/var/lib/containers" 2>/dev/null
}

check_commands
prepare_disk
format_and_create_subvolumes
mount_partitions
install_system
cleanup_temp_and_resize_root
umount_all
sudo sync
exit 0
