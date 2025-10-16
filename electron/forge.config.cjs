const path = require('path');

module.exports = {
  packagerConfig: {
    // Pack the JavaScript app as asar, but ship Python sources and requirements
    asar: true,
    icon: path.resolve(__dirname, 'assets', 'icon.ico'),
    // Include Python source tree and requirements in the installed resources folder
    extraResource: [
      path.resolve(__dirname, '..', 'src'),
      path.resolve(__dirname, '..', 'requirements.txt'),
      // Include branding and sprites so splash/logo assets resolve in packaged app
      path.resolve(__dirname, '..', 'assets')
    ],
    out: path.resolve(__dirname, 'build')
  },
  rebuildConfig: {},
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'NeoMemeMarkets',
        authors: 'Snapwave333',
        description: 'NeoMeme Markets - Meme-coin trading desktop app (Electron + PySide6)',
        setupExe: 'NeoMemeMarkets-Setup.exe',
        setupIcon: path.resolve(__dirname, 'assets/icon.ico'),
        iconUrl: 'https://raw.githubusercontent.com/Snapwave333/membot/main/electron/assets/icon.ico',
        noMsi: true,
      },
    },
    {
      name: '@electron-forge/maker-zip',
      platforms: ['win32']
    },
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-auto-unpack-natives',
      config: {}
    }
  ],
};


