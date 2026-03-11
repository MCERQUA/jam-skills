import {Config} from '@remotion/cli/config';
import path from 'path';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// CRF 18 = high quality. Default produces unwatchable bitrates at 1080p.
Config.setCrf(18);

// Force webpack to use the LOCAL copy of React (not the global React 19 from pnpm global store).
// Without this, pnpm's symlink structure causes webpack to resolve React 19 for some @remotion/* packages
// while the project uses React 18, causing "ReactCurrentBatchConfig" crash.
const projectDir = process.cwd();
const localReact = path.join(projectDir, 'node_modules', '.pnpm', 'react@18.3.1', 'node_modules', 'react');
const localReactDom = path.join(projectDir, 'node_modules', '.pnpm', 'react-dom@18.3.1_react@18.3.1', 'node_modules', 'react-dom');

Config.overrideWebpackConfig((config) => {
  return {
    ...config,
    resolve: {
      ...config.resolve,
      alias: {
        ...config.resolve?.alias,
        'react': localReact,
        'react-dom': localReactDom,
        'react/jsx-runtime': path.join(localReact, 'jsx-runtime'),
        'react/jsx-dev-runtime': path.join(localReact, 'jsx-dev-runtime'),
      },
    },
  };
});
