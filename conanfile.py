import os
from conans import ConanFile, CMake, tools


class PahocConan(ConanFile):
    name = "paho-c"
    version = "1.2.0"
    license = "EPL-1.0"
    homepage = "https://github.com/eclipse/paho.mqtt.c"
    description = """The Eclipse Paho project provides open-source client implementations of MQTT
and MQTT-SN messaging protocols aimed at new, existing, and emerging applications for the Internet
of Things (IoT)"""
    topics = ("MQTT", "IoT", "eclipse", "SSL", "paho", "C")
    url = "https://github.com/conan-community/conan-paho-c"
    author = "Conan Community"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "SSL": [True, False],
               "asynchronous": [True, False]}
    default_options = {"shared": False,
                       "fPIC": True,
                       "SSL": False,
                       "asynchronous": True}
    generators = "cmake"
    exports = "LICENSE"

    @property
    def _source_subfolder(self):
        return "sources"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        tools.get("%s/archive/v%s.zip" % (self.homepage, self.version))
        os.rename("paho.mqtt.c-%s" % self.version, self._source_subfolder)
        cmakelists_path = "%s/CMakeLists.txt" % self._source_subfolder
        tools.replace_in_file(cmakelists_path,
                              "PROJECT(\"paho\" C)",
                              """PROJECT("paho" C)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()""")
        tools.replace_in_file(cmakelists_path, "ADD_SUBDIRECTORY(test)", "")
        tools.replace_in_file(cmakelists_path,
                              "ADD_DEFINITIONS(-D_CRT_SECURE_NO_DEPRECATE -DWIN32_LEAN_AND_MEAN -MD)",
                              "ADD_DEFINITIONS(-D_CRT_SECURE_NO_DEPRECATE -DWIN32_LEAN_AND_MEAN)")

    def requirements(self):
        if self.options.SSL:
            self.requires("OpenSSL/1.0.2n@conan/stable")

    def build(self):
        cmake = CMake(self)
        cmake.definitions["PAHO_BUILD_DOCUMENTATION"] = False
        cmake.definitions["PAHO_BUILD_SAMPLES"] = False
        cmake.definitions["PAHO_BUILD_DEB_PACKAGE"] = False
        cmake.definitions["PAHO_BUILD_STATIC"] = not self.options.shared
        cmake.definitions["PAHO_WITH_SSL"] = self.options.SSL
        cmake.configure(source_folder=self._source_subfolder)
        cmake.build()

    def package(self):
        self.copy("edl-v10", src=self._source_subfolder, dst="licenses", keep_path=False)
        self.copy("epl-v10", src=self._source_subfolder, dst="licenses", keep_path=False)
        self.copy("notice.html", src=self._source_subfolder, dst="licenses", keep_path=False)
        self.copy("*.h", dst="include", src="%s/src" % self._source_subfolder)
        pattern_name = "*paho-mqtt3"
        pattern_ssl = "s" if self.options.SSL else ""
        pattern_async = "a" if self.options.asynchronous else "c"
        pattern_shared = "-static" if not self.options.shared else ""
        pattern = pattern_name + pattern_ssl + pattern_async + pattern_shared
        for extension in [".a", ".dll.a", ".lib", ".dll", ".dylib", ".*.dylib", ".so*"]:
            self.copy(pattern + extension, dst="bin" if extension.endswith("dll") else "lib",
                      keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.libs.append("ws2_32")
                if self.settings.compiler == "gcc":
                    self.cpp_info.libs.append("wsock32") # (MinGW) needed?
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
