#!/usr/bin/env bash

if [[ $OSI_USE_ENCRYPTION -eq 0 ]];then
    ROOT_PART=$(sudo blkid -o device -t PARTLABEL=alt-root) || quit_on_err "Root раздел не найден"
else
    ROOT_PART="/dev/mapper/alt-root"
fi
EFI_PART=$(sudo blkid -o device -t PARTLABEL=alt-efi) || quit_on_err "EFI раздел не найден"
BOOT_PART=$(sudo blkid -o device -t PARTLABEL=alt-boot) || quit_on_err "Boot раздел не найден"

find_ostree_deploy() {
    DEPLOY_DIR="/mnt/target/ostree/deploy/default/deploy"
    [[ ! -d "$DEPLOY_DIR" ]] && quit_on_err "Директория $DEPLOY_DIR не найдена"
    for entry in "$DEPLOY_DIR"/*; do
        if [[ -d "$entry" && "$(basename "$entry")" == *.0 ]]; then
            OSTREE_DEPLOY="$entry"
            break
        fi
    done
    [[ -z "$OSTREE_DEPLOY" ]] && quit_on_err "Не найден OSTree deploy"
}

configure_system() {
    UUID_ROOT=$(sudo blkid -s UUID -o value "$ROOT_PART") || quit_on_err "Не удалось получить UUID root"
    UUID_BOOT=$(sudo blkid -s UUID -o value "$BOOT_PART") || quit_on_err "Не удалось получить UUID boot"
    UUID_EFI=$(sudo blkid -s UUID -o value "$EFI_PART") || quit_on_err "Не удалось получить UUID EFI"

    read -r firstname _ <<< "$OSI_USER_NAME"

    sudo mount --mkdir -o rw,subvol=@ "$ROOT_PART" "/mnt/target" || quit_on_err "Ошибка монтирования корневого подтома"
    sudo mount --mkdir -o subvol=@var "$ROOT_PART" "/mnt/btrfs/var" || quit_on_err "Ошибка монтирования подтома @var"
    sudo mount --mkdir -o subvol=@home "$ROOT_PART" "/mnt/btrfs/home" || quit_on_err "Ошибка монтирования подтома @home"

    find_ostree_deploy

    sudo chroot "$OSTREE_DEPLOY" ln -sf "/usr/share/zoneinfo/${OSI_TIMEZONE}" /etc/localtime || quit_on_err "Ошибка настройки таймзоны"

    sudo chroot "$OSTREE_DEPLOY" /usr/sbin/adduser -m -d "/var/home/${firstname}" -G wheel "$firstname" || quit_on_err "Ошибка создания пользователя"
    sudo chroot "$OSTREE_DEPLOY" sh -c "echo '${firstname}:${OSI_USER_PASSWORD}' | /usr/sbin/chpasswd" || quit_on_err "Ошибка установки пароля для пользователя"
    sudo chroot "$OSTREE_DEPLOY" sh -c "echo 'root:${OSI_USER_PASSWORD}' | /usr/sbin/chpasswd" || quit_on_err "Ошибка установки пароля для root"
    sudo chroot "$OSTREE_DEPLOY" sh -c "[ -d /etc/skel ] && cp -r /etc/skel/. /var/home/${firstname}/" || quit_on_err "Ошибка копирования skel"
    sudo chroot "$OSTREE_DEPLOY" chown -R "${firstname}:${firstname}" "/var/home/${firstname}" || quit_on_err "Ошибка смены владельца домашней директории"

    sudo сhroot "$OSTREE_DEPLOY" sh -c "echo 'LANG=$OSI_LOCALE' > /etc/locale.conf"

    sudo rsync -aHAX "$OSTREE_DEPLOY/var/" "/mnt/btrfs/var/" || quit_on_err "Ошибка копирования /var"
    sudo rsync -aHAX "$OSTREE_DEPLOY/home/" "/mnt/btrfs/home/" || quit_on_err "Ошибка копирования /home"
    sudo rm -rf "$OSTREE_DEPLOY/var"
    var_deploy_path="$(dirname "$(dirname "$OSTREE_DEPLOY")")/var"
    sudo rm -rf "$var_deploy_path/*" || quit_on_err "Ошибка очистки /ostree/deploy/default/var"
    sudo touch "$var_deploy_path/.ostree-selabeled" || quit_on_err "Ошибка создания файла .ostree-selabeled"

    sudo mount --mkdir -o rw "$BOOT_PART" "/mnt/target/boot" || quit_on_err "Ошибка монтирования Boot"
    sudo mount --mkdir -o rw "$EFI_PART" "/mnt/target/boot/efi" || quit_on_err "Ошибка монтирования EFI"

    FSTAB_CONTENT="# Auto-generated fstab\n"
    FSTAB_CONTENT+="UUID=${UUID_ROOT} / btrfs subvol=@,compress=zstd:1,x-systemd.device-timeout=0 0 0\n"
    FSTAB_CONTENT+="UUID=${UUID_ROOT} /home btrfs subvol=@home,compress=zstd:1,x-systemd.device-timeout=0 0 0\n"
    FSTAB_CONTENT+="UUID=${UUID_ROOT} /var btrfs subvol=@var,compress=zstd:1,x-systemd.device-timeout=0 0 0\n"
    FSTAB_CONTENT+="UUID=${UUID_BOOT} /boot ext4 defaults 1 2\n"
    FSTAB_CONTENT+="UUID=${UUID_EFI} /boot/efi vfat umask=0077,shortname=winnt 0 2\n"

    echo -e "$FSTAB_CONTENT" | sudo tee "$OSTREE_DEPLOY/etc/fstab" 2>/dev/null
}

umount_all() {
    sudo umount "/mnt/target/boot/efi" 2>/dev/null
    sudo umount "/mnt/target/boot" 2>/dev/null
    sudo umount "/mnt/target" 2>/dev/null
    sudo umount "/mnt/btrfs/var" 2>/dev/null
    sudo umount "/mnt/btrfs/home" 2>/dev/null
    sudo umount "/var/lib/containers" 2>/dev/null
    if [[ "$OSI_USE_ENCRYPTION" -eq 1 ]];then
        sudo cryptsetup close alt-root 2>/dev/null
    fi
}

configure_system
umount_all
sudo sync
exit 0
