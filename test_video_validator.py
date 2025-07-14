import pytest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
import video_validator


class TestVideoValidator:
    
    def setup_method(self):
        self.valid_file_path = "test_video.mp4"
        self.invalid_file_path = "nonexistent.mp4"
        
        self.valid_probe_data = {
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 1920,
                    'height': 1080
                }
            ],
            'format': {
                'duration': '30.0'
            }
        }
        
        # Mock probe data for invalid video (no video stream)
        self.invalid_probe_data_no_video = {
            'streams': [
                {
                    'codec_type': 'audio',
                    'codec_name': 'aac'
                }
            ],
            'format': {
                'duration': '30.0'
            }
        }
        
        # Mock probe data for invalid dimensions
        self.invalid_probe_data_dimensions = {
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 100,  # Too small
                    'height': 100   # Too small
                }
            ],
            'format': {
                'duration': '30.0'
            }
        }


class TestHasValidFileExtension(TestVideoValidator):
    
    def test_valid_extensions(self):
        valid_files = [
            "video.mp4", "movie.avi", "clip.mov", "film.mkv",
            "video.wmv", "clip.flv", "movie.webm", "video.m4v",
            "clip.3gp", "movie.ogv", "video.mpg", "clip.mpeg",
            "movie.ts", "video.mts"
        ]
        
        for file_path in valid_files:
            assert video_validator.has_valid_file_extension(file_path)
    
    def test_invalid_extensions(self):
        invalid_files = [
            "document.txt", "image.jpg", "audio.mp3", "archive.zip",
            "video.xyz", "file.doc", "image.png", "audio.wav"
        ]
        
        for file_path in invalid_files:
            assert not video_validator.has_valid_file_extension(file_path)
    
    def test_case_insensitive_extensions(self):
        case_variations = [
            "video.MP4", "movie.AVI", "clip.MOV", "film.MKV"
        ]
        
        for file_path in case_variations:
            assert video_validator.has_valid_file_extension(file_path)


class TestGetProbeData(TestVideoValidator):
    
    @patch('video_validator.ffmpeg.probe')
    def test_successful_probe(self, mock_probe):
        mock_probe.return_value = self.valid_probe_data
        
        result = video_validator.get_probe_data(self.valid_file_path)
        
        assert result == self.valid_probe_data
        mock_probe.assert_called_once_with(self.valid_file_path)
    
    @patch('video_validator.ffmpeg.probe')
    def test_ffmpeg_error(self, mock_probe):
        mock_probe.side_effect = video_validator.ffmpeg.Error('cmd', 'stdout', 'stderr')
        
        result = video_validator.get_probe_data(self.valid_file_path)
        
        assert result is None
    
    @patch('video_validator.ffmpeg.probe')
    def test_general_exception(self, mock_probe):
        mock_probe.side_effect = Exception("General error")
        
        result = video_validator.get_probe_data(self.valid_file_path)
        
        assert result is None


class TestHasVideoStream(TestVideoValidator):
    
    def test_valid_video_stream(self):
        result = video_validator.has_video_stream(self.valid_probe_data)
        assert result is True
    
    def test_no_video_stream(self):
        result = video_validator.has_video_stream(self.invalid_probe_data_no_video)
        assert result is False
    
    def test_only_image_streams(self):
        image_probe_data = {
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'mjpeg'
                },
                {
                    'codec_type': 'video',
                    'codec_name': 'png'
                }
            ]
        }
        
        result = video_validator.has_video_stream(image_probe_data)
        assert result is False
    
    def test_mixed_streams(self):
        mixed_probe_data = {
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'mjpeg'
                },
                {
                    'codec_type': 'video',
                    'codec_name': 'h264'
                }
            ]
        }
        
        result = video_validator.has_video_stream(mixed_probe_data)
        assert result is True


class TestIsValidDuration(TestVideoValidator):
    
    def test_valid_duration(self):
        result = video_validator.is_valid_duration(self.valid_probe_data)
        assert result is True
    
    def test_minimum_duration(self):
        probe_data = {
            'format': {
                'duration': str(video_validator.MIN_DURATION)
            }
        }
        
        result = video_validator.is_valid_duration(probe_data)
        assert result is True
    
    def test_maximum_duration(self):
        probe_data = {
            'format': {
                'duration': str(video_validator.MAX_DURATION)
            }
        }
        
        result = video_validator.is_valid_duration(probe_data)
        assert result is True
    
    def test_duration_too_short(self):
        probe_data = {
            'format': {
                'duration': str(video_validator.MIN_DURATION - 1)
            }
        }
        
        result = video_validator.is_valid_duration(probe_data)
        assert result is False
    
    def test_duration_too_long(self):
        probe_data = {
            'format': {
                'duration': str(video_validator.MAX_DURATION + 1)
            }
        }
        
        result = video_validator.is_valid_duration(probe_data)
        assert result is False
    
    def test_missing_duration(self):
        probe_data = {
            'format': {}
        }
        
        result = video_validator.is_valid_duration(probe_data)
        assert result is False
    
    def test_invalid_duration_format(self):
        probe_data = {
            'format': {
                'duration': 'invalid'
            }
        }
        
        result = video_validator.is_valid_duration(probe_data)
        assert result is False


class TestIsValidDimensions(TestVideoValidator):
    
    def test_valid_dimensions(self):
        result = video_validator.is_valid_dimensions(self.valid_probe_data)
        assert result is True
    
    def test_minimum_dimensions(self):
        probe_data = {
            'streams': [
                {
                    'width': video_validator.MIN_WIDTH,
                    'height': video_validator.MIN_HEIGHT
                }
            ]
        }
        
        result = video_validator.is_valid_dimensions(probe_data)
        assert result is True
    
    def test_maximum_dimensions(self):
        probe_data = {
            'streams': [
                {
                    'width': video_validator.MAX_WIDTH,
                    'height': video_validator.MAX_HEIGHT
                }
            ]
        }
        
        result = video_validator.is_valid_dimensions(probe_data)
        assert result is True
    
    def test_width_too_small(self):
        probe_data = {
            'streams': [
                {
                    'width': video_validator.MIN_WIDTH - 1,
                    'height': video_validator.MIN_HEIGHT
                }
            ]
        }
        
        result = video_validator.is_valid_dimensions(probe_data)
        assert result is False
    
    def test_width_too_large(self):
        probe_data = {
            'streams': [
                {
                    'width': video_validator.MAX_WIDTH + 1,
                    'height': video_validator.MIN_HEIGHT
                }
            ]
        }
        
        result = video_validator.is_valid_dimensions(probe_data)
        assert result is False
    
    def test_height_too_small(self):
        probe_data = {
            'streams': [
                {
                    'width': video_validator.MIN_WIDTH,
                    'height': video_validator.MIN_HEIGHT - 1
                }
            ]
        }
        
        result = video_validator.is_valid_dimensions(probe_data)
        assert result is False
    
    def test_height_too_large(self):
        probe_data = {
            'streams': [
                {
                    'width': video_validator.MIN_WIDTH,
                    'height': video_validator.MAX_HEIGHT + 1
                }
            ]
        }
        
        result = video_validator.is_valid_dimensions(probe_data)
        assert result is False


class TestIsValidFilesize(TestVideoValidator):
    
    @patch('video_validator.os.path.getsize')
    def test_valid_filesize_small_file(self, mock_getsize):
        mock_getsize.return_value = 1000000  # 1MB
        
        result = video_validator.is_valid_filesize(self.valid_file_path)
        
        assert result is True
        mock_getsize.assert_called_once_with(self.valid_file_path)
    
    @patch('video_validator.os.path.getsize')
    def test_valid_filesize_at_limit(self, mock_getsize):
        mock_getsize.return_value = video_validator.MAX_FILESIZE
        
        result = video_validator.is_valid_filesize(self.valid_file_path)
        
        assert result is True
        mock_getsize.assert_called_once_with(self.valid_file_path)
    
    @patch('video_validator.os.path.getsize')
    def test_valid_filesize_just_under_limit(self, mock_getsize):
        mock_getsize.return_value = video_validator.MAX_FILESIZE - 1
        
        result = video_validator.is_valid_filesize(self.valid_file_path)
        
        assert result is True
        mock_getsize.assert_called_once_with(self.valid_file_path)
    
    @patch('video_validator.os.path.getsize')
    def test_invalid_filesize_exceeds_limit(self, mock_getsize):
        mock_getsize.return_value = video_validator.MAX_FILESIZE + 1
        
        result = video_validator.is_valid_filesize(self.valid_file_path)
        
        assert result is False
        mock_getsize.assert_called_once_with(self.valid_file_path)
    
    @patch('video_validator.os.path.getsize')
    def test_invalid_filesize_large_file(self, mock_getsize):
        mock_getsize.return_value = 5000000000  # 5GB
        
        result = video_validator.is_valid_filesize(self.valid_file_path)
        
        assert result is False
        mock_getsize.assert_called_once_with(self.valid_file_path)
    
    @patch('video_validator.os.path.getsize')
    def test_filesize_zero_bytes(self, mock_getsize):
        mock_getsize.return_value = 0
        
        result = video_validator.is_valid_filesize(self.valid_file_path)
        
        assert result is True
        mock_getsize.assert_called_once_with(self.valid_file_path)
    
    def test_filesize_with_nonexistent_file(self):
        with pytest.raises(OSError):
            video_validator.is_valid_filesize("nonexistent_file.mp4")


class TestIsValidVideoFile(TestVideoValidator):
    
    @patch('video_validator.os.path.exists')
    def test_file_does_not_exist(self, mock_exists):
        mock_exists.return_value = False
        
        result = video_validator.is_valid_video_file(self.invalid_file_path)
        
        assert result is False
        mock_exists.assert_called_once_with(self.invalid_file_path)
    
    @patch('video_validator.os.path.exists')
    @patch('video_validator.has_valid_file_extension')
    def test_invalid_file_extension(self, mock_extension, mock_exists):
        mock_exists.return_value = True
        mock_extension.return_value = False
        
        result = video_validator.is_valid_video_file("test.txt")
        
        assert result is False
    
    @patch('video_validator.os.path.exists')
    @patch('video_validator.has_valid_file_extension')
    @patch('video_validator.get_probe_data')
    def test_probe_data_none(self, mock_probe, mock_extension, mock_exists):
        mock_exists.return_value = True
        mock_extension.return_value = True
        mock_probe.return_value = None
        
        result = video_validator.is_valid_video_file(self.valid_file_path)
        
        assert result is False
    
    @patch('video_validator.os.path.exists')
    @patch('video_validator.has_valid_file_extension')
    @patch('video_validator.get_probe_data')
    @patch('video_validator.has_video_stream')
    @patch('video_validator.is_valid_duration')
    @patch('video_validator.is_valid_dimensions')
    def test_all_validations_pass(self, mock_dimensions, mock_duration, 
                                  mock_stream, mock_probe, mock_extension, mock_exists):
        mock_exists.return_value = True
        mock_extension.return_value = True
        mock_probe.return_value = self.valid_probe_data
        mock_stream.return_value = True
        mock_duration.return_value = True
        mock_dimensions.return_value = True
        
        result = video_validator.is_valid_video_file(self.valid_file_path)
        
        assert result is True
    
    @patch('video_validator.os.path.exists')
    @patch('video_validator.has_valid_file_extension')
    @patch('video_validator.get_probe_data')
    @patch('video_validator.has_video_stream')
    def test_video_stream_validation_fails(self, mock_stream, mock_probe, 
                                          mock_extension, mock_exists):
        mock_exists.return_value = True
        mock_extension.return_value = True
        mock_probe.return_value = self.valid_probe_data
        mock_stream.return_value = False
        
        result = video_validator.is_valid_video_file(self.valid_file_path)
        
        assert result is False


class TestConstants(TestVideoValidator):
    
    def test_constants_exist(self):
        assert hasattr(video_validator, 'VALID_VIDEO_EXTENSIONS')
        assert hasattr(video_validator, 'MIN_WIDTH')
        assert hasattr(video_validator, 'MAX_WIDTH')
        assert hasattr(video_validator, 'MIN_HEIGHT')
        assert hasattr(video_validator, 'MAX_HEIGHT')
        assert hasattr(video_validator, 'MIN_DURATION')
        assert hasattr(video_validator, 'MAX_DURATION')
        assert hasattr(video_validator, 'MAX_FILESIZE')
    
    def test_valid_extensions_list(self):
        expected_extensions = [
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', 
            '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg', '.ts', '.mts'
        ]
        
        for ext in expected_extensions:
            assert ext in video_validator.VALID_VIDEO_EXTENSIONS
    
    def test_dimension_constraints(self):
        assert video_validator.MAX_WIDTH > video_validator.MIN_WIDTH
        assert video_validator.MAX_HEIGHT > video_validator.MIN_HEIGHT
        assert video_validator.MIN_WIDTH > 0
        assert video_validator.MIN_HEIGHT > 0
    
    def test_duration_constraints(self):
        assert video_validator.MAX_DURATION > video_validator.MIN_DURATION
        assert video_validator.MIN_DURATION > 0
    
    def test_filesize_constraint(self):
        assert video_validator.MAX_FILESIZE > 0
        assert video_validator.MAX_FILESIZE == 2000000000  # 2GB


if __name__ == '__main__':
    pytest.main([__file__])
