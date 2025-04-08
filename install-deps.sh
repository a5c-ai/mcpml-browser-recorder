# if linux:
if [ "$(uname)" == "Linux" ]; then
    sudo apt-get install libwoff1\
         libopus0\
         libharfbuzz-icu0\
         libenchant-2-2\
         libsecret-1-0\
         libhyphen0\
         libegl1\
         libevdev2\
         libgles2\
         gstreamer1.0-libav
else if [ "$(uname)" == "Darwin" ]; then
    brew install libwoff1\
         libopus0\
         libharfbuzz-icu0\
         libenchant-2-2\
         libsecret-1-0\
         libhyphen0\
         libegl1\
         libevdev2\
         libgles2\
         gstreamer
else
    echo "Not supported on this platform"
fi
pip install -r requirements.txt
playwright install
