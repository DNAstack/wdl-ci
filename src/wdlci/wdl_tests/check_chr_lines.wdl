version 1.0

# Check if lines start with "chr" in input files
# Input type: File

task check_chr_lines {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		current_run_output_not_chr_lines_count=$(sed -E '/@HD|@SQ/d' ~{current_run_output} | grep -cv "^chr" || [[ $? == 1 ]])
		validated_output_not_chr_lines_count=$(sed -E '/@HD|@SQ/d' ~{validated_output} | grep -cv "^chr" || [[ $? == 1 ]])

		if [[ "$validated_output_not_chr_lines_count" != 0 ]]; then
			err "Some lines do not start with 'chr' in validated output: [~{basename(validated_output)}]. Count: [$validated_output_not_chr_lines_count]"
			exit 1
		fi

		if [[ "$current_run_output_not_chr_lines_count" != "$validated_output_not_chr_lines_count" ]]; then
			err "Lines that do not start with 'chr' present:
				Expected output: [$validated_output_not_chr_lines_count]
				Current run output: [$current_run_output_not_chr_lines_count]"
			exit 1
		else
			echo "All lines start with 'chr'. Lines without 'chr' count: [$current_run_output_not_chr_lines_count]"
		fi
	>>>

	output {
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
