// iPhone HDR (HLG / Dolby Vision) -> SDR Rec.709 ProRes 422 HQ, rotation baked in, Apple's own tone mapping.
// swift hdr_to_sdr.swift <in.mov> <out.mov>
import AVFoundation

let args = CommandLine.arguments
let asset = AVURLAsset(url: URL(fileURLWithPath: args[1]))
let out = URL(fileURLWithPath: args[2])
try? FileManager.default.removeItem(at: out)

let sem = DispatchSemaphore(value: 0)
Task {
    do {
        let track = try await asset.loadTracks(withMediaType: .video)[0]
        let comp = try await AVMutableVideoComposition.videoComposition(withPropertiesOf: asset)
        comp.colorPrimaries = AVVideoColorPrimaries_ITU_R_709_2
        comp.colorTransferFunction = AVVideoTransferFunction_ITU_R_709_2
        comp.colorYCbCrMatrix = AVVideoYCbCrMatrix_ITU_R_709_2
        let size = comp.renderSize
        let reader = try AVAssetReader(asset: asset)
        let rout = AVAssetReaderVideoCompositionOutput(videoTracks: [track], videoSettings: [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_422YpCbCr10,
            AVVideoColorPropertiesKey: [
                AVVideoColorPrimariesKey: AVVideoColorPrimaries_ITU_R_709_2,
                AVVideoTransferFunctionKey: AVVideoTransferFunction_ITU_R_709_2,
                AVVideoYCbCrMatrixKey: AVVideoYCbCrMatrix_ITU_R_709_2]])
        rout.videoComposition = comp
        reader.add(rout)
        let writer = try AVAssetWriter(outputURL: out, fileType: .mov)
        let win = AVAssetWriterInput(mediaType: .video, outputSettings: [
            AVVideoCodecKey: AVVideoCodecType.proRes422HQ,
            AVVideoWidthKey: size.width, AVVideoHeightKey: size.height,
            AVVideoColorPropertiesKey: [
                AVVideoColorPrimariesKey: AVVideoColorPrimaries_ITU_R_709_2,
                AVVideoTransferFunctionKey: AVVideoTransferFunction_ITU_R_709_2,
                AVVideoYCbCrMatrixKey: AVVideoYCbCrMatrix_ITU_R_709_2]])
        win.expectsMediaDataInRealTime = false
        writer.add(win)
        reader.startReading(); writer.startWriting(); writer.startSession(atSourceTime: .zero)
        var n = 0
        while let sb = rout.copyNextSampleBuffer() {
            while !win.isReadyForMoreMediaData { usleep(2000) }
            win.append(sb); n += 1
        }
        win.markAsFinished()
        await writer.finishWriting()
        print("frames \(n), size \(size), status \(writer.status.rawValue) \(writer.error?.localizedDescription ?? "")")
    } catch { print("error: \(error)") }
    sem.signal()
}
sem.wait()
