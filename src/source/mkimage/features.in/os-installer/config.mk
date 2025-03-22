use/os-installer: 
	@$(call add_feature)
	@$(call add,LIVE_PACKAGES,git podman fuse-overlayfs btrfs-progs skopeo sudo vte python3-module-yaml udisks2 glibc-locales)
	@$(call try,GLOBAL_LIVE_INSTALL,1)
