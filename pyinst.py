#!/usr/bin/env python3

# This code is based on yt-dlp source code

import os
import platform
import shutil
import sys

from PyInstaller.__main__ import run as run_pyinstaller

import utils as ut


def read_file(fname):
    with open(fname, encoding='utf-8') as f:
        return f.read()


# Get the version without importing the package
def read_version(fname='version.py'):
    exec(compile(read_file(fname), fname, 'exec'))
    return locals()['__version__']


OS_NAME, MACHINE, ARCH = sys.platform, platform.machine().lower(), platform.architecture()[0][:2]
if MACHINE in ('x86', 'x86_64', 'amd64', 'i386', 'i686'):
    MACHINE = 'x86' if ARCH == '32' else ''


def main():
    opts, version = parse_options(), read_version()

    onedir = '--onedir' in opts or '-D' in opts
    if not onedir and '-F' not in opts and '--onefile' not in opts:
        opts.append('--onefile')

    name, final_file = exe(onedir)
    print(f'Building yt-cut v{version} for {OS_NAME} {platform.machine()} with options {opts}')
    print('Remember to update the version using  "devscripts/update-version.py"')
    print(f'Destination: {final_file}\n')

    opts = [
        f'--name={name}',
        '--windowed',
        '--icon=icons/ytcut.png',
        '--upx-exclude=vcruntime140.dll',
        '--noconfirm',
        *opts,
        'main.py',
    ]

    print(f'Running PyInstaller with {opts}')
    run_pyinstaller(opts)
    set_version_info(final_file, version)

    from pathlib import Path
    dist = Path(final_file).parent
    print("Coping package files")
    copy_all_needs(dist)
    print("Making archive")
    make_archive(dist, version)


def parse_options():
    # Compatibility with older arguments
    opts = sys.argv[1:]
    if opts[0:1] in (['32'], ['64']):
        if ARCH != opts[0]:
            raise Exception(f'{opts[0]}bit executable cannot be built on a {ARCH}bit system')
        opts = opts[1:]
    return opts


def exe(onedir):
    """@returns (name, path)"""
    name = '_'.join(filter(None, (
        'yt-cut',
        {'win32': '', 'darwin': 'macos'}.get(OS_NAME, OS_NAME),
        MACHINE,
    )))
    return name, ''.join(filter(None, (
        'dist/',
        onedir and f'{name}/',
        name,
        OS_NAME == 'win32' and '.exe'
    )))


def version_to_list(version):
    version_list = version.split('.')
    return list(map(int, version_list)) + [0] * (4 - len(version_list))


def set_version_info(exe, version):
    if OS_NAME == 'win32':
        windows_set_version(exe, version)


def windows_set_version(exe, version):
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

    try:
        from PyInstaller.utils.win32.versioninfo import SetVersion
    except ImportError:  # Pyinstaller >= 5.8
        from PyInstaller.utils.win32.versioninfo import write_version_info_to_executable as SetVersion

    version_list = version_to_list(version)
    suffix = MACHINE and f'_{MACHINE}'
    SetVersion(exe, VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=version_list,
            prodvers=version_list,
            mask=0x3F,
            flags=0x0,
            OS=0x4,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo([StringTable('040904B0', [
                StringStruct('Comments', 'yt-cut%s GUI Interface' % suffix),
                StringStruct('CompanyName', 'https://github.com/yt-dlp'),
                StringStruct('FileDescription', 'yt-cut%s' % (MACHINE and f' ({MACHINE})')),
                StringStruct('FileVersion', version),
                StringStruct('InternalName', f'yt-cut{suffix}'),
                StringStruct('LegalCopyright', 'pukkandan.ytcut@gmail.com | UNLICENSE'),
                StringStruct('OriginalFilename', f'yt-cut{suffix}.exe'),
                StringStruct('ProductName', f'yt-cut{suffix}'),
                StringStruct(
                    'ProductVersion', f'{version}{suffix} on Python {platform.python_version()}'),
            ])]), VarFileInfo([VarStruct('Translation', [0, 1200])])
        ]
    ))


def copy_all_needs(dist):
    shutil.copytree("icons", dist/"icons", dirs_exist_ok=True)
    if ut.under_windows():
        shutil.copytree("tools", dist/"tools", dirs_exist_ok=True)


def make_archive(dist, version):
    import datetime as dt
    arch = dist.with_name("yt-cut")
    os.rename(dist, arch)
    today = dt.date.today().strftime("%Y%m%d")
    osname = {'win32': 'win10', 'darwin': 'macos'}.get(OS_NAME, OS_NAME)
    shutil.make_archive(f"yt-cut_v{version}+{today}_{osname}_x64", "zip",
                        root_dir=arch.parent, base_dir=arch, verbose=True)
    os.rename(arch, dist)    # restore the dist name


if __name__ == '__main__':
    main()
