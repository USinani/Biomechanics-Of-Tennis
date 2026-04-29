function stream_swing_udp(jsonl_path, host, port, fps, realtime)
%STREAM_SWING_UDP Replay a JSONL swing file over UDP at a fixed rate.
%
% Phase 0 scaffold: a Unity client (or any UDP listener) can subscribe to
% (host, port) and receive one JSON-encoded swing frame per packet. The
% schema is identical to export_unity_swing_jsonl, so a consumer that
% parses one parses both.
%
% Inputs:
%   jsonl_path - path to the .jsonl file produced by run_3d_forward_swing
%   host       - destination host (default '127.0.0.1')
%   port       - destination port (default 55001)
%   fps        - frame rate to emit at (default 100 Hz)
%   realtime   - logical; if true, sleep between frames to honour fps
%                (default true)
%
% Requirements:
%   MATLAB R2020b+ (udpport). If unavailable, use the legacy `udp` API.
%
% Notes:
%   * UDP packets are best-effort; large payloads may fragment. Each frame
%     is ~600-800 bytes which fits in one MTU.
%   * To verify locally: run python tools/udp_swing_listener.py first.

if nargin < 2 || isempty(host);     host = '127.0.0.1';   end
if nargin < 3 || isempty(port);     port = 55001;          end
if nargin < 4 || isempty(fps);      fps = 100;             end
if nargin < 5 || isempty(realtime); realtime = true;       end

if ~isfile(jsonl_path)
    error('stream_swing_udp:missing', 'JSONL file not found: %s', jsonl_path);
end

% Read every line.
fid = fopen(jsonl_path, 'r');
if fid < 0
    error('stream_swing_udp:open', 'Cannot read %s', jsonl_path);
end
lines = textscan(fid, '%s', 'Delimiter', '\n', 'Whitespace', '');
fclose(fid);
lines = lines{1};
N = numel(lines);
fprintf('[stream_swing_udp] %d frames -> udp://%s:%d at %d FPS (realtime=%d)\n', ...
    N, host, port, fps, realtime);

if exist('udpport', 'file') ~= 2
    error('stream_swing_udp:udpport', ...
        'udpport not available. Requires MATLAB R2020b+.');
end
u = udpport("byte");
cleanup = onCleanup(@() delete(u));

dt = 1 / fps;
t0 = tic;
for k = 1:N
    payload = uint8([lines{k} char(10)]);
    write(u, payload, "uint8", host, port);
    if realtime
        target = (k - 1) * dt;
        elapsed = toc(t0);
        if elapsed < target
            pause(target - elapsed);
        end
    end
end
fprintf('[stream_swing_udp] sent %d frames in %.2f s\n', N, toc(t0));
end
