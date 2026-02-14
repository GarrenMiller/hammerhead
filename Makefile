build:
	cargo build --release --target aarch64-linux-android

setup:
	brew install --cask android-ndk
	rustup target add aarch64-linux-android

stage:
	adb push target/aarch64-linux-android/release/hammerhead /data/local/tmp/
	adb shell chmod +x /data/local/tmp/hammerhead

run:
	adb shell /data/local/tmp/hammerhead
