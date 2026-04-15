function ensure_dir(d)
%ENSURE_DIR Create directory if it does not exist.
if isempty(d)
    return;
end
if ~exist(d, 'dir')
    mkdir(d);
end
end
