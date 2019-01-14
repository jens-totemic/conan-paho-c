import os
from conans import ConanFile, CMake, tools


class PahocConan(ConanFile):
    name = "paho-c"
    version = "1.3.0"
    license = "EPL-1.0"
    homepage = "https://github.com/eclipse/paho.mqtt.c"
    description = """The Eclipse Paho project provides open-source client implementations of MQTT
and MQTT-SN messaging protocols aimed at new, existing, and emerging applications for the Internet
of Things (IoT)"""
    url = "https://github.com/conan-community/conan-paho-c"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "SSL": [True, False],
               "async": [True, False]}
    default_options = {"shared": False, "fPIC": True, "SSL": False, "async": True}
    generators = "cmake"
    exports = "LICENSE"
    exports_sources = ["0001-fix-MinGW-and-OSX-builds.patch", "0002-fix-capath-support.patch"]
    _source_subfolder = "sources"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        tools.get("%s/archive/v%s.zip" % (self.homepage, self.version))
        os.rename("paho.mqtt.c-%s" % self.version, self._source_subfolder)
        cmakelists_path = "%s/CMakeLists.txt" % self._source_subfolder
        tools.patch(base_path=self._source_subfolder, patch_file="0001-fix-MinGW-and-OSX-builds.patch")
        # add a patch that fixes capath not working
        # from https://github.com/eclipse/paho.mqtt.c/pull/574
        # TODO: remove in paho 1.3.1
        tools.patch(base_path=self._source_subfolder, patch_file="0002-fix-capath-support.patch")
        tools.replace_in_file(cmakelists_path,
                              "PROJECT(\"Eclipse Paho C\" C)",
                              """PROJECT(\"Eclipse Paho C\" C)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()""")

    def requirements(self):
        if self.options.SSL:
            self.requires("OpenSSL/1.0.2@conan/stable")

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["PAHO_ENABLE_TESTING"] = False
        cmake.definitions["PAHO_BUILD_DOCUMENTATION"] = False
        cmake.definitions["PAHO_BUILD_SAMPLES"] = False
        cmake.definitions["PAHO_BUILD_DEB_PACKAGE"] = False
        cmake.definitions["PAHO_BUILD_STATIC"] = not self.options.shared
        cmake.definitions["PAHO_WITH_SSL"] = self.options.SSL
        cmake.configure(source_folder=self._source_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("edl-v10", src=self._source_subfolder, dst="licenses", keep_path=False)
        self.copy("epl-v10", src=self._source_subfolder, dst="licenses", keep_path=False)
        self.copy("notice.html", src=self._source_subfolder, dst="licenses", keep_path=False)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
    
        if self.options.shared and self:
            # Python 3.7 reserves async as a keyword so we can't access variable with dot 
            if getattr(self.options, "async"):
                if self.options.SSL:
                    self.cpp_info.libs = ["paho-mqtt3as"]
                else:
                    self.cpp_info.libs = ["paho-mqtt3a"]
            else:
                if self.options.SSL:
                    self.cpp_info.libs = ["paho-mqtt3cs"]
                else:
                    self.cpp_info.libs = ["paho-mqtt3c"]
        else:
            if getattr(self.options, "async"):
                if self.options.SSL:
                    self.cpp_info.libs = ["paho-mqtt3as-static"]
                else:
                    self.cpp_info.libs = ["paho-mqtt3a-static"]
            else:
                if self.options.SSL:
                    self.cpp_info.libs = ["paho-mqtt3cs-static"]
                else:
                    self.cpp_info.libs = ["paho-mqtt3c-static"]

        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.libs.append("ws2_32")
                if self.settings.compiler == "gcc":
                    self.cpp_info.libs.extend(["wsock32", "uuid", "crypt32", "rpcrt4"])
        else:
            if self.settings.os == "Linux":
                self.cpp_info.libs.append("c")
                self.cpp_info.libs.append("dl")
                self.cpp_info.libs.append("pthread")
            elif self.settings.os == "FreeBSD":
                self.cpp_info.libs.append("compat")
                self.cpp_info.libs.append("pthread")
            else:
                self.cpp_info.libs.append("c")
                self.cpp_info.libs.append("pthread")
