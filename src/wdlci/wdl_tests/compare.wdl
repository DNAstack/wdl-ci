version 1.0

task compare {
	input {
		Map[File,File] file_compares
		Map[String,String] string_compares
	}

	# TODO
	Int disk_size = 50

	command <<<
		set -euo pipefail

		# Compare files
		echo "Comparing files" | tee -a log
		while read -r file_set || [[ -n "$file_set" ]]; do
			echo "$file_set" | tee -a log
		done < ~{write_json(file_compares)}

		# Compare strings
		echo "Comparing strings" | tee -a log
		while read -r string_set || [[ -n "$string_set" ]]; do
			echo "$string_set" | tee -a log
		done < ~{write_json(string_compares)}
	>>>

	output {
		File log = "log"
	}

	runtime {
		docker: "ubuntu:xenial"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		# disks: "local-disk " + disk_size + " HDD"
		# preemptible: 1
	}
}
