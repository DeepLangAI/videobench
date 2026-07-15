// 用 AVFoundation 抽帧（本机无 ffmpeg 时的替代方案）
// 用法: swift extract_frames.swift <video.mp4> <outdir> <fps>
import AVFoundation
import AppKit

let args = CommandLine.arguments
guard args.count == 4, let fps = Double(args[3]) else {
    print("usage: swift extract_frames.swift <video> <outdir> <fps>"); exit(1)
}
let url = URL(fileURLWithPath: args[1])
let outdir = URL(fileURLWithPath: args[2])
try? FileManager.default.createDirectory(at: outdir, withIntermediateDirectories: true)

let asset = AVURLAsset(url: url)
let duration = CMTimeGetSeconds(asset.duration)
let gen = AVAssetImageGenerator(asset: asset)
gen.requestedTimeToleranceBefore = .zero
gen.requestedTimeToleranceAfter = .zero
gen.appliesPreferredTrackTransform = true

var t = 0.0
var count = 0
while t < duration {
    let time = CMTime(seconds: t, preferredTimescale: 600)
    if let cg = try? gen.copyCGImage(at: time, actualTime: nil) {
        let rep = NSBitmapImageRep(cgImage: cg)
        if let jpg = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.6]) {
            let name = String(format: "f%05.2fs.jpg", t)
            try? jpg.write(to: outdir.appendingPathComponent(name))
            count += 1
        }
    }
    t += 1.0 / fps
}
print("extracted \(count) frames from \(url.lastPathComponent) (duration \(String(format: "%.2f", duration))s)")
