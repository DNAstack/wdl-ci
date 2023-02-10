version 1.0

task calculate_md5sum {
	input {
		File input_file
	}

	Int disk_size = ceil(size(input_file, "GB") + 10)
	String input_file_basename = basename(input_file)

	command <<<
		md5sum < ~{input_file} | awk '{print $1}' > ~{input_file_basename}.md5sum
	>>>

	output {
		String md5sum = read_string("~{input_file_basename}.md5sum")
	}

	runtime {
		docker: "ubuntu:xenial"
		cpu: 1
		memory: "3.75 GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
