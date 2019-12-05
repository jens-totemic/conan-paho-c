# -*- coding: utf-8 -*-
import os
from conans import ConanFile, CMake, tools


class PahocConan(ConanFile):
    name = "paho-c"
    version = "1.3.1"
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
               "asynchronous": [True, False],
               "qos0Persistence": [True, False]}
    default_options = {"shared": False,
                       "fPIC": True,
                       "SSL": False,
                       "asynchronous": True,
                       # persisting qos0 along with all other types is the default in Paho.
                       "qos0Persistence": True}
    generators = "cmake"
    exports = "LICENSE"
    exports_sources = ["CMakeLists.txt", "0001-fix-MinGW-and-OSX-builds.patch", "0002-fix-cmake-install.patch", "0003-stop-qos0-persistence-650.patch"]

    @property
    def _source_subfolder(self):
        return "sources"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        sha256 = "96efc8b5691dc0b6b0820617113ccfffa76153b274f80d5fa4768067bf08a1b1"
        tools.get("%s/archive/v%s.zip" % (self.homepage, self.version), sha256=sha256)
        os.rename("paho.mqtt.c-%s" % self.version, self._source_subfolder)

    def requirements(self):
        if self.options.SSL:
            self.requires("openssl/1.1.1d")

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["PAHO_ENABLE_TESTING"] = False
        cmake.definitions["PAHO_BUILD_DOCUMENTATION"] = False
        cmake.definitions["PAHO_BUILD_SAMPLES"] = False
        cmake.definitions["PAHO_BUILD_STATIC"] = not self.options.shared
        cmake.definitions["PAHO_WITH_SSL"] = self.options.SSL
        cmake.definitions["PAHO_BUILD_ASYNC"] = self.options.asynchronous
        cmake.configure()
        return cmake

    def build(self):
        tools.patch(base_path=self._source_subfolder, patch_file="0001-fix-MinGW-and-OSX-builds.patch")
        tools.patch(base_path=self._source_subfolder, patch_file="0002-fix-cmake-install.patch")
        # add a patch that allows disabling persistence of QoS0 messages
        # https://github.com/eclipse/paho.mqtt.c/issues/650
        # TODO: remove if a fix is merged
        if not self.options.qos0Persistence:
            tools.patch(base_path=self._source_subfolder, patch_file="0003-stop-qos0-persistence-650.patch")
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("edl-v10", src=self._source_subfolder, dst="licenses")
        self.copy("epl-v10", src=self._source_subfolder, dst="licenses")
        self.copy("notice.html", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
    
        if self.options.shared and self:
            # Python 3.7 reserves async as a keyword so we can't access variable with dot 
            if self.options.asynchronous:
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
            if self.options.asynchronous:
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
                self.cpp_info.libs.extend(["c", "dl", "pthread"])
            elif self.settings.os == "FreeBSD":
                self.cpp_info.libs.extend(["compat", "pthread"])
            else:
                self.cpp_info.libs.extend(["c", "pthread"])
