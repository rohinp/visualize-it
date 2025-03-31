import React from 'react';
import { toPng, toJpeg, toSvg } from 'html-to-image';
import './DownloadOptions.css';

const DownloadOptions = ({ visualization }) => {
    const downloadImage = (format) => {
        const node = document.querySelector('.visualization-container');
        if (!node) return;

        const fileName = `${visualization.title.replace(/\s+/g, '-').toLowerCase()}.${format}`;

        switch (format) {
            case 'png':
                toPng(node)
                    .then(dataUrl => {
                        const link = document.createElement('a');
                        link.download = fileName;
                        link.href = dataUrl;
                        link.click();
                    })
                    .catch(err => console.error('Error downloading PNG:', err));
                break;
            case 'jpg':
                toJpeg(node)
                    .then(dataUrl => {
                        const link = document.createElement('a');
                        link.download = fileName;
                        link.href = dataUrl;
                        link.click();
                    })
                    .catch(err => console.error('Error downloading JPEG:', err));
                break;
            case 'svg':
                toSvg(node)
                    .then(dataUrl => {
                        const link = document.createElement('a');
                        link.download = fileName;
                        link.href = dataUrl;
                        link.click();
                    })
                    .catch(err => console.error('Error downloading SVG:', err));
                break;
            case 'json':
                const dataStr = JSON.stringify(visualization.data, null, 2);
                const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
                const link = document.createElement('a');
                link.download = `${visualization.title.replace(/\s+/g, '-').toLowerCase()}.json`;
                link.href = dataUri;
                link.click();
                break;
            default:
                break;
        }
    };

    return (
        <div className="download-options">
            <div className="download-buttons">
                <button className="btn-small waves-effect waves-light" onClick={() => downloadImage('png')}>
                    <i className="material-icons left">file_download</i>PNG
                </button>
                <button className="btn-small waves-effect waves-light" onClick={() => downloadImage('jpg')}>
                    <i className="material-icons left">file_download</i>JPEG
                </button>
                <button className="btn-small waves-effect waves-light" onClick={() => downloadImage('svg')}>
                    <i className="material-icons left">file_download</i>SVG
                </button>
                <button className="btn-small waves-effect waves-light" onClick={() => downloadImage('json')}>
                    <i className="material-icons left">file_download</i>JSON
                </button>
            </div>
        </div>
    );
};

export default DownloadOptions;