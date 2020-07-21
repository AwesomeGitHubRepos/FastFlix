# -*- coding: utf-8 -*-
import reusables
import re

""" ./rav1e --help
rav1e 0.3.0 (release)
AV1 video encoder

USAGE:
    rav1e [FLAGS] [OPTIONS] <INPUT> --output <OUTPUT>

FLAGS:
        --fullhelp
            Prints more detailed help information

        --low-latency
            Low latency mode; disables frame reordering
            Has a significant speed-to-quality trade-off
        --still-picture
            Still picture mode

        --benchmark
            Provide a benchmark report at the end of the encoding

    -v, --verbose
            Verbose logging; outputs info for every frame

    -q, --quiet
            Do not output any status message

        --psnr
            Calculate and display PSNR metrics

        --metrics
            Calulate and display several metrics including PSNR, SSIM, CIEDE2000 etc

    -y
            Overwrite output file.

    -h, --help
            Prints help information

    -V, --version
            Prints version information


OPTIONS:
        --threads <THREADS>
            Set the threadpool size [default: 0]

    -o, --output <OUTPUT>
            Compressed AV1 in IVF video output

        --first-pass <FIRST_PASS>
            Perform the first pass of a two-pass encode, saving the pass data to the specified file for future passes

        --second-pass <SECOND_PASS>
            Perform the second pass of a two-pass encode, reading the pass data saved from a previous pass from the
            specified file
    -l, --limit <LIMIT>
            Maximum number of frames to encode [default: 0]

        --skip <SKIP>
            Skip n number of frames and encode [default: 0]

        --quantizer <QP>
            Quantizer (0-255), smaller values are higher quality [default: 100]

        --min-quantizer <MINQP>
            Minimum quantizer (0-255) to use in bitrate mode [default: 0]

    -b, --bitrate <BITRATE>
            Bitrate (kbps)

    -s, --speed <SPEED>
            Speed level (0 is best quality, 10 is fastest)
            Speeds 10 and 0 are extremes and are generally not recommended [default: 6]
    -i, --min-keyint <MIN_KEYFRAME_INTERVAL>
            Minimum interval between keyframes [default: 12]

    -I, --keyint <KEYFRAME_INTERVAL>
            Maximum interval between keyframes. When set to 0, disables fixed-interval keyframes. [default: 240]

    -S, --switch-frame-interval <SWITCH_FRAME_INTERVAL>
            Maximum interval between switch frames. When set to 0, disables switch frames. [default: 0]

        --reservoir-frame-delay <RESERVOIR_FRAME_DELAY>
            Number of frames over which rate control should distribute the reservoir [default: min(240, 1.5x keyint)]
            A minimum value of 12 is enforced.
        --rdo-lookahead-frames <RDO_LOOKAHEAD_FRAMES>
            Number of frames encoder should lookahead for RDO purposes [default: 40]
        --tune <TUNE>
            Quality tuning [default: Psychovisual]  [possible values: Psnr, Psychovisual]

        --tile-rows <TILE_ROWS>
            Number of tile rows. Must be a power of 2. rav1e may override this based on video resolution. [default: 0]

        --tile-cols <TILE_COLS>
            Number of tile columns. Must be a power of 2. rav1e may override this based on video resolution. [default:
            0]
        --tiles <TILES>
            Number of tiles. Tile-cols and tile-rows are overridden
            so that the video has at least this many tiles. [default: 0]
        --range <PIXEL_RANGE>
            Pixel range [default: limited]  [possible values: Limited, Full]

        --primaries <COLOR_PRIMARIES>
            Color primaries used to describe color parameters [default: unspecified]  [possible values: BT709,
            Unspecified, BT470M, BT470BG, BT601, SMPTE240, GenericFilm, BT2020, XYZ, SMPTE431, SMPTE432, EBU3213]
        --transfer <TRANSFER_CHARACTERISTICS>
            Transfer characteristics used to describe color parameters [default: unspecified]  [possible values: BT709,
            Unspecified, BT470M, BT470BG, BT601, SMPTE240, Linear, Log100, Log100Sqrt10, IEC61966, BT1361, SRGB,
            BT2020_10Bit, BT2020_12Bit, SMPTE2084, SMPTE428, HLG]
        --matrix <MATRIX_COEFFICIENTS>
            Matrix coefficients used to describe color parameters [default: unspecified]  [possible values: Identity,
            BT709, Unspecified, FCC, BT470BG, BT601, SMPTE240, YCgCo, BT2020NCL, BT2020CL, SMPTE2085, ChromatNCL,
            ChromatCL, ICtCp]
        --mastering-display <MASTERING_DISPLAY>
            Mastering display primaries in the form of G(x,y)B(x,y)R(x,y)WP(x,y)L(max,min) [default: unspecified]

        --content-light <CONTENT_LIGHT>
            Content light level used to describe content luminosity (cll,fall) [default: 0,0]

        --frame-rate <FRAME_RATE>
            Constant frame rate to set at the output (inferred from input when omitted)

        --time-scale <TIME_SCALE>
            The time scale associated with the frame rate if provided (ignored otherwise) [default: 1]

    -r, --reconstruction <RECONSTRUCTION>
            Outputs a Y4M file containing the output from the decoder


ARGS:
    <INPUT>
            Uncompressed YUV4MPEG2 video input


"""
from fastflix.plugins.common.helpers import Command, generate_filters
from fastflix.plugins.common.audio import build_audio
from fastflix.plugins.common.subtitles import build_subtitle


def build(
    source,
    video_track,
    bitrate=None,
    qp=None,
    start_time=0,
    duration=None,
    audio_tracks=(),
    subtitle_tracks=(),
    disable_hdr=False,
    side_data=None,
    speed=6,
    tune="Psychovisual",
    pixel_range="Limited",
    color_primaries="Unspecified",
    matrix="Unspecified",
    transfer="Unspecified",
    **kwargs,
):
    filters = generate_filters(**kwargs)
    audio = build_audio(audio_tracks)
    subtitles = build_subtitle(subtitle_tracks)

    # "ffmpeg -i [input.mp4] -nostdin -f rawvideo -pix_fmt yuv420p - | SvtAv1EncApp.exe -i stdin -n [number_of_frames_to_encode] -w [width] -h [height]"
    # "ffmpeg -i input.mov -f yuv4mpegpipe - | rav1e - --output out.ivf"

    # ffmpeg -i 20200702_195828.mp4 -t 5 -f yuv4mpegpipe -s 1920x1080 -pix_fmt yuv420p - | ./rav1e - --speed 10 --output test.ivf

    command = (
        f'"{{ffmpeg}}" -y '
        f' {f"-ss {start_time}" if start_time else ""}  '
        f'{f"-t {duration}" if duration else ""} '
        f'-i "{source}" '
        f"{filters}"
        f"-map 0:{video_track} "
        "-f yuv4mpegpipe -pix_fmt yuv420p - | "
        "{rav1e} - -y"
        f"--speed {speed}"
        '--output "<tempfile.1.ivf>"'  # {output}"
    )

    audio_file = "<tempfile.2.mkv>"

    command_audio = Command(
        (
            f'"{{ffmpeg}}" -y '
            f'{f"-ss {start_time}" if start_time else ""} '
            f'{f"-t {duration - start_time}" if duration else ""} '
            f'-i "{source}" '
            f'{audio} {subtitles} "{audio_file}"'
        ),
        ["ffmpeg"],
        False,
        exe="ffmpeg",
        name="Split audio at proper time offsets into new file",
    )

    command_3 = Command(
        (
            f'"{{ffmpeg}}" -y '
            f'-i "<tempfile.1.ivf>" -i "{audio_file}" '
            f'{"-map_metadata -1 -shortest -reset_timestamps 1" if start_time or duration else ""} '
            f"-c copy -map 0:v -map 1:a "
            # -af "aresample=async=1:min_hard_comp=0.100000:first_pts=0"
            f'"{{output}}"'
        ),
        ["ffmpeg", "output"],
        False,
        exe="ffmpeg",
        name="Combine audio and video files into MKV container",
    )

    return [Command(command, ["ffmpeg", "rav1e"], False, name="Single Pass QP"), command_audio, command_3]
    # beginning = re.sub("[ ]+", " ", beginning)
    #
    # if bitrate:
    #     command_1 = f'{beginning} -passlogfile "<tempfile.1.log>" -b:v {bitrate} -pass 1 -an -f matroska {ending}'
    #     command_2 = f'{beginning} -passlogfile "<tempfile.1.log>" -b:v {bitrate} -pass 2 {audio} "{{output}}"'
    #     return [
    #         helpers.Command(command_1, ["ffmpeg", "output"], False, name="First Pass bitrate"),
    #         helpers.Command(command_2, ["ffmpeg", "output"], False, name="Second Pass bitrate"),
    #     ]
    # elif crf:
    #     command_1 = f'{beginning} -b:v 0 -crf {crf} {audio} "{{output}}"'
    #     return [helpers.Command(command_1, ["ffmpeg", "output"], False, name="Single Pass CRF")]
