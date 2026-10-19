using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Database.Migrations
{
    /// <inheritdoc />
    public partial class CreatePopPortalSchema : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropPrimaryKey(
                name: "PK_Users",
                table: "Users");

            migrationBuilder.RenameTable(
                name: "Users",
                newName: "User");

            migrationBuilder.RenameColumn(
                name: "user_level",
                table: "User",
                newName: "is_active");

            migrationBuilder.RenameIndex(
                name: "IX_Users_user_email",
                table: "User",
                newName: "IX_User_user_email");

            migrationBuilder.AddColumn<DateTime>(
                name: "created_at_utc",
                table: "User",
                type: "TEXT",
                nullable: false,
                defaultValue: new DateTime(1, 1, 1, 0, 0, 0, 0, DateTimeKind.Unspecified));

            migrationBuilder.AddColumn<DateTime>(
                name: "updated_at_utc",
                table: "User",
                type: "TEXT",
                nullable: false,
                defaultValue: new DateTime(1, 1, 1, 0, 0, 0, 0, DateTimeKind.Unspecified));

            migrationBuilder.AddColumn<string>(
                name: "user_role",
                table: "User",
                type: "TEXT",
                maxLength: 20,
                nullable: false,
                defaultValue: "");

            // O esquema anterior usava user_level como indicador de administrador.
            // Converte os registros existentes para os valores do novo MER.
            migrationBuilder.Sql("""
                UPDATE "User"
                SET user_role = CASE WHEN is_active = 1 THEN 'admin' ELSE 'basic' END,
                    is_active = 1,
                    created_at_utc = CURRENT_TIMESTAMP,
                    updated_at_utc = CURRENT_TIMESTAMP;
                """);

            migrationBuilder.AddPrimaryKey(
                name: "PK_User",
                table: "User",
                column: "user_id");

            migrationBuilder.CreateTable(
                name: "Department",
                columns: table => new
                {
                    department_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    department_name = table.Column<string>(type: "TEXT", maxLength: 120, nullable: false),
                    department_code = table.Column<string>(type: "TEXT", maxLength: 30, nullable: false),
                    is_active = table.Column<bool>(type: "INTEGER", nullable: false),
                    created_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false),
                    updated_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Department", x => x.department_id);
                });

            migrationBuilder.CreateTable(
                name: "Link",
                columns: table => new
                {
                    link_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    link_path = table.Column<string>(type: "TEXT", maxLength: 1000, nullable: false),
                    created_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false),
                    updated_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Link", x => x.link_id);
                });

            migrationBuilder.CreateTable(
                name: "Pop",
                columns: table => new
                {
                    pop_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    created_by = table.Column<int>(type: "INTEGER", nullable: false),
                    updated_by = table.Column<int>(type: "INTEGER", nullable: true),
                    pop_title = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false),
                    pop_description = table.Column<string>(type: "TEXT", nullable: true),
                    pop_file_path = table.Column<string>(type: "TEXT", maxLength: 500, nullable: true),
                    pop_version = table.Column<string>(type: "TEXT", maxLength: 50, nullable: true),
                    pop_status = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    created_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false),
                    updated_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Pop", x => x.pop_id);
                    table.ForeignKey(
                        name: "FK_Pop_User_created_by",
                        column: x => x.created_by,
                        principalTable: "User",
                        principalColumn: "user_id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Pop_User_updated_by",
                        column: x => x.updated_by,
                        principalTable: "User",
                        principalColumn: "user_id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "UserDepartment",
                columns: table => new
                {
                    user_department_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    user_id = table.Column<int>(type: "INTEGER", nullable: false),
                    department_id = table.Column<int>(type: "INTEGER", nullable: false),
                    access_type = table.Column<string>(type: "TEXT", maxLength: 30, nullable: false),
                    valid_from_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false),
                    expires_at_utc = table.Column<DateTime>(type: "TEXT", nullable: true),
                    revoked_at_utc = table.Column<DateTime>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserDepartment", x => x.user_department_id);
                    table.ForeignKey(
                        name: "FK_UserDepartment_Department_department_id",
                        column: x => x.department_id,
                        principalTable: "Department",
                        principalColumn: "department_id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_UserDepartment_User_user_id",
                        column: x => x.user_id,
                        principalTable: "User",
                        principalColumn: "user_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Checklist",
                columns: table => new
                {
                    checklist_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    pop_id = table.Column<int>(type: "INTEGER", nullable: false),
                    user_id = table.Column<int>(type: "INTEGER", nullable: false),
                    checklist_description = table.Column<string>(type: "TEXT", nullable: true),
                    created_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false),
                    completed_at_utc = table.Column<DateTime>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Checklist", x => x.checklist_id);
                    table.ForeignKey(
                        name: "FK_Checklist_Pop_pop_id",
                        column: x => x.pop_id,
                        principalTable: "Pop",
                        principalColumn: "pop_id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Checklist_User_user_id",
                        column: x => x.user_id,
                        principalTable: "User",
                        principalColumn: "user_id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "Feedback",
                columns: table => new
                {
                    feedback_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    user_id = table.Column<int>(type: "INTEGER", nullable: false),
                    pop_id = table.Column<int>(type: "INTEGER", nullable: true),
                    answered_by = table.Column<int>(type: "INTEGER", nullable: true),
                    feedback_description = table.Column<string>(type: "TEXT", nullable: false),
                    feedback_status = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    feedback_answer = table.Column<string>(type: "TEXT", nullable: true),
                    created_at_utc = table.Column<DateTime>(type: "TEXT", nullable: false),
                    answered_at_utc = table.Column<DateTime>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Feedback", x => x.feedback_id);
                    table.ForeignKey(
                        name: "FK_Feedback_Pop_pop_id",
                        column: x => x.pop_id,
                        principalTable: "Pop",
                        principalColumn: "pop_id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_Feedback_User_answered_by",
                        column: x => x.answered_by,
                        principalTable: "User",
                        principalColumn: "user_id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Feedback_User_user_id",
                        column: x => x.user_id,
                        principalTable: "User",
                        principalColumn: "user_id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "PopDepartment",
                columns: table => new
                {
                    pop_department_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    pop_id = table.Column<int>(type: "INTEGER", nullable: false),
                    department_id = table.Column<int>(type: "INTEGER", nullable: false),
                    access_type = table.Column<string>(type: "TEXT", maxLength: 30, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PopDepartment", x => x.pop_department_id);
                    table.ForeignKey(
                        name: "FK_PopDepartment_Department_department_id",
                        column: x => x.department_id,
                        principalTable: "Department",
                        principalColumn: "department_id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_PopDepartment_Pop_pop_id",
                        column: x => x.pop_id,
                        principalTable: "Pop",
                        principalColumn: "pop_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "PopLink",
                columns: table => new
                {
                    pop_link_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    pop_id = table.Column<int>(type: "INTEGER", nullable: false),
                    link_id = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PopLink", x => x.pop_link_id);
                    table.ForeignKey(
                        name: "FK_PopLink_Link_link_id",
                        column: x => x.link_id,
                        principalTable: "Link",
                        principalColumn: "link_id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_PopLink_Pop_pop_id",
                        column: x => x.pop_id,
                        principalTable: "Pop",
                        principalColumn: "pop_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "StandardCheck",
                columns: table => new
                {
                    standard_check_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    pop_id = table.Column<int>(type: "INTEGER", nullable: false),
                    check_text = table.Column<string>(type: "TEXT", nullable: false),
                    check_order = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_StandardCheck", x => x.standard_check_id);
                    table.ForeignKey(
                        name: "FK_StandardCheck_Pop_pop_id",
                        column: x => x.pop_id,
                        principalTable: "Pop",
                        principalColumn: "pop_id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ChecklistItemResult",
                columns: table => new
                {
                    checklist_item_result_id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    checklist_id = table.Column<int>(type: "INTEGER", nullable: false),
                    standard_check_id = table.Column<int>(type: "INTEGER", nullable: false),
                    is_checked = table.Column<bool>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ChecklistItemResult", x => x.checklist_item_result_id);
                    table.ForeignKey(
                        name: "FK_ChecklistItemResult_Checklist_checklist_id",
                        column: x => x.checklist_id,
                        principalTable: "Checklist",
                        principalColumn: "checklist_id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ChecklistItemResult_StandardCheck_standard_check_id",
                        column: x => x.standard_check_id,
                        principalTable: "StandardCheck",
                        principalColumn: "standard_check_id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Checklist_pop_id",
                table: "Checklist",
                column: "pop_id");

            migrationBuilder.CreateIndex(
                name: "IX_Checklist_user_id",
                table: "Checklist",
                column: "user_id");

            migrationBuilder.CreateIndex(
                name: "IX_ChecklistItemResult_checklist_id_standard_check_id",
                table: "ChecklistItemResult",
                columns: new[] { "checklist_id", "standard_check_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ChecklistItemResult_standard_check_id",
                table: "ChecklistItemResult",
                column: "standard_check_id");

            migrationBuilder.CreateIndex(
                name: "IX_Department_department_code",
                table: "Department",
                column: "department_code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Feedback_answered_by",
                table: "Feedback",
                column: "answered_by");

            migrationBuilder.CreateIndex(
                name: "IX_Feedback_pop_id",
                table: "Feedback",
                column: "pop_id");

            migrationBuilder.CreateIndex(
                name: "IX_Feedback_user_id",
                table: "Feedback",
                column: "user_id");

            migrationBuilder.CreateIndex(
                name: "IX_Pop_created_by",
                table: "Pop",
                column: "created_by");

            migrationBuilder.CreateIndex(
                name: "IX_Pop_updated_by",
                table: "Pop",
                column: "updated_by");

            migrationBuilder.CreateIndex(
                name: "IX_PopDepartment_department_id",
                table: "PopDepartment",
                column: "department_id");

            migrationBuilder.CreateIndex(
                name: "IX_PopDepartment_pop_id_department_id",
                table: "PopDepartment",
                columns: new[] { "pop_id", "department_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_PopLink_link_id",
                table: "PopLink",
                column: "link_id");

            migrationBuilder.CreateIndex(
                name: "IX_PopLink_pop_id_link_id",
                table: "PopLink",
                columns: new[] { "pop_id", "link_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_StandardCheck_pop_id_check_order",
                table: "StandardCheck",
                columns: new[] { "pop_id", "check_order" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_UserDepartment_department_id",
                table: "UserDepartment",
                column: "department_id");

            migrationBuilder.CreateIndex(
                name: "IX_UserDepartment_user_id_department_id",
                table: "UserDepartment",
                columns: new[] { "user_id", "department_id" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "ChecklistItemResult");

            migrationBuilder.DropTable(
                name: "Feedback");

            migrationBuilder.DropTable(
                name: "PopDepartment");

            migrationBuilder.DropTable(
                name: "PopLink");

            migrationBuilder.DropTable(
                name: "UserDepartment");

            migrationBuilder.DropTable(
                name: "Checklist");

            migrationBuilder.DropTable(
                name: "StandardCheck");

            migrationBuilder.DropTable(
                name: "Link");

            migrationBuilder.DropTable(
                name: "Department");

            migrationBuilder.DropTable(
                name: "Pop");

            migrationBuilder.DropPrimaryKey(
                name: "PK_User",
                table: "User");

            migrationBuilder.DropColumn(
                name: "created_at_utc",
                table: "User");

            migrationBuilder.DropColumn(
                name: "updated_at_utc",
                table: "User");

            migrationBuilder.DropColumn(
                name: "user_role",
                table: "User");

            migrationBuilder.RenameTable(
                name: "User",
                newName: "Users");

            migrationBuilder.RenameColumn(
                name: "is_active",
                table: "Users",
                newName: "user_level");

            migrationBuilder.RenameIndex(
                name: "IX_User_user_email",
                table: "Users",
                newName: "IX_Users_user_email");

            migrationBuilder.AddPrimaryKey(
                name: "PK_Users",
                table: "Users",
                column: "user_id");
        }
    }
}
