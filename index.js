import {execa} from 'execa';
import readline from 'readline';
import EventEmitter from 'eventemitter3';
import randomstring from 'randomstring';
import PQueue from 'p-queue';
import got from 'got';
import fs from 'node:fs';
import tmp from 'tmp-promise';
import {promisify} from 'node:util';
import stream from 'node:stream';
const pipeline = promisify(stream.pipeline);
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const latest = {
    ts: -1
}
async function getLatest(maxage) {
    maxage = maxage || 1000 * 60 * 60 * 24;
    const now = new Date().getTime();
    if (now > latest.ts + maxage) {
        const {fd, path:ytdlpPath} = await tmp.file();
        await pipeline(
            got.stream('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp'),
            fs.createWriteStream(ytdlpPath),
        );
        latest.ts = now;
        latest.ytdlpPath = ytdlpPath
    } else {
        console.log('using cached yt-dlp');
    }
    return latest.ytdlpPath;
}

export default class YtDlp extends EventEmitter {
    constructor({ytdlpPath, ffmpegPath, pythonPath, verbose=false} = {}) {
        super();
        this.queue = new PQueue({concurrency: 1});
        this.process = execa(pythonPath || 'python', [path.join(__dirname, 'ydlserver.py'), JSON.stringify({ytdlpPath, ffmpegPath})]);
        if (verbose) {
            this.process.stderr.pipe(process.stderr);
        }
        this.linereader = readline.createInterface({
            input: this.process.stdout
        });
        this.linereader.on('line', this.parseLine.bind(this));
        this._isReady = new Promise((resolve, reject) => {
            this.on('ready', () => {
                resolve(true);
            })
        });
    }

    static async withLatest({ffmpegPath, pythonPath, maxage, verbose=false} = {}) {
        const ytdlpPath = await getLatest(maxage);
        const obj = new YtDlp({ytdlpPath, ffmpegPath, pythonPath, verbose});
        await obj.waitForReady();
        return obj;
    }

    async waitForReady() {
        return this._isReady;
    }

    parseLine(line) {
        let response;
        try {
            response = JSON.parse(line)
        } catch (err) {
            throw err;
        }
        this.emit(response.type, response);
    }

    async _command(command, options, callbacks) {
        await this.waitForReady();
        return await this.queue.add(() => {
            return new Promise((resolve, reject) => {
                const id = randomstring.generate();
                const payload = Object.assign({}, options, {command, id});
                if (callbacks instanceof Object) {
                    for (let eventType in callbacks) {
                        this.on(eventType, response => {
                            if (response.id !== id) return;
                            callbacks[eventType](response.data);
                        })
                    }
                }
                this.on(command, function handleResponse(response) {
                    if (response.id !== id) return;
                    this.removeListener(command, handleResponse, this);
                    if (response.data.error) {
                        reject(response.data);
                    } else {
                        resolve(response.data);
                    }
                }, this);
                this._send(payload);
            });
        });
    }
    
    _send(payload) {
        this.process.stdin.write(JSON.stringify(payload)+'\n');
    }

    async download(url, {format='bv*+ba/b', path='.', ydlOpts, onProgress} = {}) {
        const options = Object.assign({format}, ydlOpts);
        const callbacks = {};
        if (onProgress) {
            callbacks.progress = onProgress;
        }
        const response = await this._command('download', {url, options}, callbacks);
        return response.info
    }

    async info(url, {format='bv*+ba/b', ydlOpts} = {}) {
        const options = Object.assign({format}, ydlOpts);
        const response = await this._command('info', {url, options});
        return response.info;
    }

    async stop() {
        this.linereader.removeAllListeners();
        this.process.cancel();
        await process
    }
}