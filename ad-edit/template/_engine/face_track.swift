// Face positions with Apple Vision, every `step` seconds -> JSON [{t, cx, cy, w, h}] in pixels (top-left origin).
// face_track <in.mov> <out.json> [step=0.2]
import AVFoundation
import Vision

let a = CommandLine.arguments
let asset = AVURLAsset(url: URL(fileURLWithPath: a[1]))
let step = a.count > 3 ? Double(a[3])! : 0.2
let gen = AVAssetImageGenerator(asset: asset)
gen.appliesPreferredTrackTransform = true
gen.requestedTimeToleranceBefore = .zero
gen.requestedTimeToleranceAfter = .zero
let dur = CMTimeGetSeconds(asset.duration)
var rows: [[String: Double]] = []
var t = 0.0
while t < dur {
    if let img = try? gen.copyCGImage(at: CMTime(seconds: t, preferredTimescale: 600), actualTime: nil) {
        let W = Double(img.width), H = Double(img.height)
        let req = VNDetectFaceRectanglesRequest()
        try? VNImageRequestHandler(cgImage: img).perform([req])
        if let f = (req.results ?? []).max(by: { $0.boundingBox.width < $1.boundingBox.width }) {
            let b = f.boundingBox
            rows.append(["t": t, "cx": (b.midX) * W, "cy": (1 - b.midY) * H, "w": b.width * W, "h": b.height * H])
        }
    }
    t += step
}
let data = try! JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted])
try! data.write(to: URL(fileURLWithPath: a[2]))
print("faces \(rows.count)")
