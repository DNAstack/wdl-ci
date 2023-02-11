version 1.0

task compare {
	input {
		Map[File,File] file_compares
		Map[String,String] string_compares
	}

	# TODO
	Int disk_size = 50

	# TODO actually compare
	command <<<
		set -euo pipefail

		apt-get -qq update && apt-get -qq install jq

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
			exit 1
		}

		# Compare files
		echo "Comparing files"
		jq -r 'keys[] as $k | "\($k)\t\(.[$k])"' < ~{write_json(file_compares)} \
		| while read -r file_set || [[ -n "$file_set" ]]; do
			current_run_output=$(echo "$file_set" | cut -f 1)
			validated_output=$(echo "$file_set" | cut -f 2)

			# md5sum files
			current_run_md5sum=$(md5sum "$current_run_output" | cut -d ' ' -f 1)
			validated_output_md5sum=$(md5sum "$validated_output" | cut -d ' ' -f 1)
			if [[ "$current_run_md5sum" != "$validated_output_md5sum" ]]; then
				err "File md5sums did not match:\n\tExpected md5sum: [$validated_output_md5sum]\n\tCurrent run md5sum: [$current_run_md5sum]"
			else
				echo "File md5sums matched for file [$(basename "$validated_output")]"
			fi
		done

		# Compare strings
		echo "Comparing strings"
		jq -r 'keys[] as $k | "\($k)\t\(.[$k])"' < ~{write_json(string_compares)} \
		| while read -r string_set || [[ -n "$string_set" ]]; do
			current_run_output=$(echo "$string_set" | cut -f 1)
			validated_output=$(echo "$string_set" | cut -f 2)

			# compare string equality
			if [[ "$current_run_output" != "$validated_output" ]]; then
				err "String mismatch:\n\tExpected string: [$validated_output]\n\tCurrent run string: [$current_run_output]"
			else
				echo "Strings matched [$validated_output]"
			fi
		done
	>>>

	output {
		Int rc = read_int("rc")
	}

	runtime {
		docker: "ubuntu:xenial"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
