version 1.0

# Check if input files are sorted by coordinates
# Input type: VCF/BCF

task check_sorted_vcf_bcf {
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

		bcftools view --header-only ~{validated_output} | grep "##contig" > validated_header_contig.txt
		bcftools view --header-only ~{current_run_output} | grep "##contig" | sort > current_header_contig.txt

		if cmp -s "validated_header_contig.txt" "current_header_contig.txt"; then
			err "Current run output: [~{basename(current_run_output)}] is not sorted"
			exit 1
		else
			echo "Current run output: [~{basename(current_run_output)}] is sorted"
		fi
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.0.1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
