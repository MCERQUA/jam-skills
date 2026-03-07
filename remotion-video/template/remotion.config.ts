import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// CRF 18 = high quality. Default produces unwatchable bitrates at 1080p.
Config.setCrf(18);
