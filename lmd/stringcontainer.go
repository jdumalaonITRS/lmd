package main

import (
	"bytes"
	"compress/gzip"
	"io/ioutil"
)

// DefaultCompressionMinimumSize sets the default minimum number of characters to use compression
const DefaultCompressionMinimumSize = 500

// CompressionMinimumSize sets the minimum number of characters to use compression
var CompressionMinimumSize = DefaultCompressionMinimumSize

// CompressionLevel sets the minimum number of characters to use compression
var CompressionLevel = gzip.DefaultCompression

// StringContainer wraps large strings
type StringContainer struct {
	StringData     string
	CompressedData *[]byte
}

// NewStringContainer returns a new StringContainer
func NewStringContainer(data *string) *StringContainer {
	c := &StringContainer{}
	c.Set(data)
	return c
}

// Set sets the current string
func (s *StringContainer) Set(data *string) {
	// it only makes sense to compress larger strings
	if len(*data) < CompressionMinimumSize {
		s.StringData = *data
		s.CompressedData = nil
		return
	}
	s.StringData = ""
	var b bytes.Buffer
	gz, _ := gzip.NewWriterLevel(&b, CompressionLevel)
	gz.Write([]byte(*data))
	gz.Close()
	by := b.Bytes()
	s.CompressedData = &by
	if log.IsV(LogVerbosityTrace) {
		log.Tracef("compressed string from %d to %d (%.1f%%)", len(*data), len(s.StringData), 100-(float64(len(s.StringData))/float64(len(*data))*100))
	}
}

// String returns the string data
func (s *StringContainer) String() string {
	if s.CompressedData == nil {
		return s.StringData
	}
	return *s.StringRef()
}

// StringRef returns the string data
func (s *StringContainer) StringRef() *string {
	if s.CompressedData == nil {
		return &s.StringData
	}
	r, err := gzip.NewReader(bytes.NewReader(*s.CompressedData))
	if err != nil {
		log.Errorf("failed to create gzip reader: %s", err.Error())
		str := ""
		return &str
	}
	b, err := ioutil.ReadAll(r)
	r.Close()
	if err != nil {
		log.Errorf("failed to read compressed data: %s", err.Error())
		str := ""
		return &str
	}
	str := string(b)
	return &str
}
