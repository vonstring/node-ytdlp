# ytdlp-helper

ytdlp-helper is a Node.js module that provides a simple interface for downloading and retrieving information from YouTube videos using the `yt-dlp` command-line tool.

## Features

- Download YouTube videos in various formats
- Retrieve video information such as title, description, and duration
- Utilizes the `yt-dlp` command-line tool for video processing
- Supports caching of the latest `yt-dlp` version for faster execution

## Installation

To use YtDlp in your project, you need to install it using npm:

```bash
npm install --save ytdlp-helper
```

## Usage

```javascript
import YtDlp from ytdlp-helper;

(async () => {
  const ytdlp = await YtDlp.withLatest();
  
  // Download video
  const videoInfo = await ytdlp.download('https://www.youtube.com/watch?v=dQw4w9WgXcQ', {
    format: 'bv*+ba/b',
    path: './downloads',
    onProgress: (progress) => {
      console.log(`Progress: ${progress.percent}%`);
    }
  });

  // Get video information
  const info = await ytdlp.info('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
  console.log(info);

  // Stop the YtDlp instance
  await ytdlp.stop();
})();
```

## API Reference

### YtDlp

#### constructor(options)

Creates a new YtDlp instance.

- `options`: An object containing the following properties:
  - `ytdlpPath`: (Optional) Path to the `yt-dlp` executable. Defaults to the latest version.
  - `ffmpegPath`: (Optional) Path to the `ffmpeg` executable.
  - `pythonPath`: (Optional) Path to the Python executable.
  - `verbose`: (Optional) Enable verbose logging. Defaults to `false`.

#### withLatest(options)

Creates a new YtDlp instance with the latest `yt-dlp` version.

- `options`: An object containing the following properties:
  - `ffmpegPath`: (Optional) Path to the `ffmpeg` executable.
  - `pythonPath`: (Optional) Path to the Python executable.
  - `maxage`: (Optional) Maximum age of the cached `yt-dlp` version in milliseconds. Defaults to 24 hours.
  - `verbose`: (Optional) Enable verbose logging. Defaults to `false`.

#### download(url, options)

Downloads a YouTube video.

- `url`: URL of the video to download.
- `options`: An object containing the following properties:
  - `format`: (Optional) Video format. Defaults to 'bv*+ba/b'.
  - `path`: (Optional) Output path for the downloaded video. Defaults to the current working directory.
  - `ydlOpts`: (Optional) Additional options to pass to `yt-dlp`.
  - `onProgress`: (Optional) A callback function to handle progress updates.

#### info(url, options)

Retrieves information about a YouTube video.

- `url`: URL of the video to get information from.
- `options`: An object containing the following properties:
  - `format`: (Optional) Video format. Defaults to 'bv*+ba/b'.
  - `ydlOpts`: (Optional) Additional options to pass to `yt-dlp`.

#### stop()

Stops the YtDlp instance and cleans up resources.

## License

This project is licensed under the MIT License.