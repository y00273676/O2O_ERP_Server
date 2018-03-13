#! SHELL=/bin/sh

supervisorctl = /home/work/supervisor/bin/supervisorctl

android_restart:
	@for port in {9600..9603}; \
	do\
		${supervisorctl} restart android:android-$$port; \
	done

android_restart1:
	@for port in {9600..9600}; \
	do\
		${supervisorctl} restart android:android-$$port; \
	done

test:
	python -m tests
