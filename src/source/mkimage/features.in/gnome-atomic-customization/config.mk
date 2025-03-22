use/gnome-atomic-customization:
	@$(call add_feature)
	@$(call add,LIVE_PACKAGES,htop fastfetch nvtop notify-send zsh zsh-completions starship bash-completion inxi openssh-server iucode_tool systemd-ssh-agent ptyxis zram-generator)
	@$(call add,LIVE_PACKAGES,gnome-shell-extension-appindicator gnome-shell-extension-dash-to-dock)
	@$(call add,LIVE_PACKAGES,gtk3-theme-adw-gtk3 pinentry-gnome3 gnome-icon-theme gnome-icon-theme-symbolic gnome-themes-extra libgtk2-engine-adwaita fonts-otf-abattis-cantarell fonts-ttf-cjkuni-ukai fonts-ttf-liberation fonts-ttf-dejavu)
	@$(call add,LIVE_PACKAGES,nautilus-python gvfs-backends fuse-gvfs nautilus-share samba-usershares file-roller)
	@$(call add,LIVE_PACKAGES,glibc-locales)
