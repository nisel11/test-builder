ifeq (distro,$(IMAGE_CLASS))

distro/regular-gnome-atomic: distro/.regular-x11 mixin/regular-gnome \
	+plymouth use/browser/firefox mixin/regular-desktop \
	use/firmware/laptop +systemd +systemd-optimal +vmguest \
	use/services/bluetooth-enable use/live/rescue \
	use/vmguest/dri use/branding/full \
	use/gnome-atomic-customization use/os-installer
	@$(call set,GRUB_DEFAULT,live)
	@$(call set,SYSLINUX_DEFAULT,live)
ifeq (,$(filter-out i586 x86_64,$(ARCH)))
	@$(call add,THE_PACKAGES,xorg-drv-vmware) # for virtualbox with VMSVGA
endif
	@$(call add,THE_PACKAGES,bluez)

endif

